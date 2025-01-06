package main

import (
    "bufio"
    "fmt"
    "os"
    "sort"
    "strings"
    "text/tabwriter"
    "time"

    splunk "github.com/pvik/go-splunk-rest"
    "github.com/spf13/cobra"
    "golang.org/x/term"
)

// formatResultsTable converts Splunk query results into a formatted table
func formatResultsTable(results []map[string]interface{}) {
    if len(results) == 0 {
        fmt.Println("No results to display")
        return
    }

    // Collect all unique headers
    headers := make(map[string]bool)
    for _, result := range results {
        for key := range result {
            headers[key] = true
        }
    }

    // Convert headers to sorted slice
    headerSlice := make([]string, 0, len(headers))
    for header := range headers {
        headerSlice = append(headerSlice, header)
    }
    sort.Strings(headerSlice)

    // Create tabwriter
    w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
    defer w.Flush()

    // Write headers
    fmt.Fprintln(w, strings.Join(headerSlice, "\t"))

    // Write separator
    separator := make([]string, len(headerSlice))
    for i := range separator {
        separator[i] = strings.Repeat("-", len(headerSlice[i]))
    }
    fmt.Fprintln(w, strings.Join(separator, "\t"))

    // Write data rows
    for _, result := range results {
        row := make([]string, len(headerSlice))
        for i, header := range headerSlice {
            if val, exists := result[header]; exists {
                switch v := val.(type) {
                case string:
                    row[i] = v
                case float64:
                    row[i] = fmt.Sprintf("%.2f", v)
                case int:
                    row[i] = fmt.Sprintf("%d", v)
                default:
                    row[i] = fmt.Sprintf("%v", v)
                }
            } else {
                row[i] = "-"
            }
        }
        fmt.Fprintln(w, strings.Join(row, "\t"))
    }
}

// executeSearch performs a Splunk search with standard options
func executeSearch(conn splunk.Connection, searchQuery string) ([]map[string]interface{}, error) {
    searchOptions := splunk.SearchOptions{
        MaxCount:        100,
        UseEarliestTime: true,
        EarliestTime:    time.Now().Add(-30 * 24 * time.Hour),
        UseLatestTime:   true,
        LatestTime:      time.Now(),
    }

    return conn.Search(searchQuery, searchOptions)
}

// createSearchCommand creates a cobra command for a specific search type
func createSearchCommand(name, description, searchQuery string) *cobra.Command {
    return &cobra.Command{
        Use:   name,
        Short: description,
        Run: func(cmd *cobra.Command, args []string) {
            // We'll set this in main()
            splunkConn := cmd.Context().Value("splunkConn").(splunk.Connection)
            
            fmt.Printf("Executing %s query...\n", name)
            recs, err := executeSearch(splunkConn, searchQuery)
            if err != nil {
                fmt.Printf("Error executing query: %v\n", err)
                return
            }
            
            fmt.Printf("\n%s Results:\n", strings.Title(name))
            formatResultsTable(recs)
        },
    }
}

func main() {
    fmt.Println("Splunk CLI - Interactive Query Tool")
    fmt.Println("-----------------------------------")

    // Get credentials
    fmt.Print("Enter Splunk username: ")
    reader := bufio.NewReader(os.Stdin)
    username, _ := reader.ReadString('\n')
    username = strings.TrimSpace(username)

    fmt.Print("Enter Splunk password: ")
    bytePassword, _ := term.ReadPassword(int(os.Stdin.Fd()))
    fmt.Println()
    password := strings.TrimSpace(string(bytePassword))

    // Initialize Splunk connection
    splunkConn := splunk.Connection{
        Host:     "https://splunk-server:8089",
        AuthType: "basic",
        Username: username,
        Password: password,
    }

    // Test connection
    _, err := executeSearch(splunkConn, "search index=_internal | head 1")
    if err != nil {
        fmt.Printf("Failed to connect to Splunk: %v\n", err)
        os.Exit(1)
    }
    fmt.Println("Successfully authenticated to Splunk!")

    // Create root command
    rootCmd := &cobra.Command{
        Use:   "splunk-cli",
        Short: "CLI to interact with Splunk using go-splunk-rest",
    }

    // Add search commands
    searches := map[string]string{
        "query-user": "search index=_internal sourcetype=user_data | stats count by user",
        "query-group": "search index=_internal sourcetype=group_data | stats count by group",
        "query-failures": "search index=_internal sourcetype=error_logs | stats count by error",
    }

    for name, query := range searches {
        cmd := createSearchCommand(name, fmt.Sprintf("Query %s data", strings.TrimPrefix(name, "query-")), query)
        rootCmd.AddCommand(cmd)
    }

    // Add help command
    rootCmd.AddCommand(&cobra.Command{
        Use:   "help",
        Short: "Display help information",
        Run: func(cmd *cobra.Command, args []string) {
            fmt.Println("\nAvailable Commands:")
            fmt.Println("  query-user      Query user data")
            fmt.Println("  query-group     Query group data")
            fmt.Println("  query-failures  Query failure data")
            fmt.Println("  help            Display this help message")
            fmt.Println("  exit            Exit the program")
        },
    })

    // Main command loop
    fmt.Println("\nType 'help' for available commands or 'exit' to quit")
    for {
        fmt.Print("\nsplunk-cli> ")
        input, _ := reader.ReadString('\n')
        input = strings.TrimSpace(input)

        if input == "exit" {
            fmt.Println("Exiting Splunk CLI. Goodbye!")
            break
        }

        if input == "" {
            continue
        }

        args := strings.Split(input, " ")
        rootCmd.SetArgs(args)
        if err := rootCmd.Execute(); err != nil {
            fmt.Printf("Error: %v\n", err)
        }
    }
}
