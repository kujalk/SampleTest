package main

import (
    "bufio"
    "fmt"
    "math"
    "os"
    "sort"
    "strings"
    "text/tabwriter"
    "time"
    "strconv"

    splunk "github.com/pvik/go-splunk-rest"
    "github.com/spf13/cobra"
    "runtime"
    "golang.org/x/sys/windows"
    "golang.org/x/term"
)

var globalSplunkConn splunk.Connection

type SearchParams struct {
    authType string
    target   string
}

// formatResultsTable remains the same
func formatResultsTable(results []map[string]interface{}) {
    if len(results) == 0 {
        fmt.Println("No results to display")
        return
    }

    headers := make(map[string]bool)
    for _, result := range results {
        for key := range result {
            headers[key] = true
        }
    }

    headerSlice := make([]string, 0, len(headers))
    for header := range headers {
        headerSlice = append(headerSlice, header)
    }
    sort.Strings(headerSlice)

    w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
    defer w.Flush()

    fmt.Fprintln(w, strings.Join(headerSlice, "\t"))

    separator := make([]string, len(headerSlice))
    for i := range separator {
        separator[i] = strings.Repeat("-", len(headerSlice[i]))
    }
    fmt.Fprintln(w, strings.Join(separator, "\t"))

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

// New function to format stats results with ASCII visualization
func formatStatsResults(results []map[string]interface{}) {
    if len(results) == 0 {
        fmt.Println("No results to display")
        return
    }

    // Initialize color variables
    var enableColors bool
    if runtime.GOOS == "windows" {
        // Enable virtual terminal processing on Windows
        stdout := windows.Handle(os.Stdout.Fd())
        var originalMode uint32
        windows.GetConsoleMode(stdout, &originalMode)
        windows.SetConsoleMode(stdout, originalMode|windows.ENABLE_VIRTUAL_TERMINAL_PROCESSING)
        enableColors = true
    } else {
        // For non-Windows systems, check if output is a terminal
        enableColors = term.IsTerminal(int(os.Stdout.Fd()))
    }

    // Extract pass/fail counts
    var total int
    counts := map[string]int{
        "pass": 0,
        "fail": 0,
    }
    
    for _, result := range results {
        category := result["result"].(string)
        count, _ := strconv.Atoi(result["count"].(string))
        counts[category] = count
        total += count
    }

    fmt.Println("\nPass/Fail Statistics:")
    fmt.Println("--------------------")

    chartWidth := 50
    fmt.Println("\nDistribution Chart:")
    
    // Define color codes
    var green, red, reset string
    if enableColors {
        green = "\x1b[32m"
        red = "\x1b[31m"
        reset = "\x1b[0m"
    }

    categories := []string{"pass", "fail"}
    colors := map[string]string{
        "pass": green,
        "fail": red,
    }
    
    for _, category := range categories {
        count := counts[category]
        percentage := (float64(count) / float64(total)) * 100
        bars := int(math.Round((percentage / 100) * float64(chartWidth)))
        
        bar := strings.Repeat("█", bars)
        
        // Only apply colors if enabled
        if enableColors {
            fmt.Printf("%s%-6s %s%s%s %5.1f%% (%d)\n",
                colors[category],
                strings.Title(category),
                bar,
                reset,
                strings.Repeat(" ", chartWidth-bars),
                percentage,
                count)
        } else {
            fmt.Printf("%-6s %s%s %5.1f%% (%d)\n",
                strings.Title(category),
                bar,
                strings.Repeat(" ", chartWidth-bars),
                percentage,
                count)
        }
    }

    fmt.Println("\nSummary Table:")
    w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
    defer w.Flush()

    fmt.Fprintln(w, "Status\tCount\tPercentage")
    fmt.Fprintln(w, "------\t-----\t----------")
    
    for _, category := range categories {
        count := counts[category]
        percentage := (float64(count) / float64(total)) * 100
        fmt.Fprintf(w, "%s\t%d\t%.1f%%\n",
            strings.Title(category),
            count,
            percentage)
    }
    fmt.Fprintf(w, "Total\t%d\t100.0%%\n", total)
}
    
func executeSearch(conn splunk.Connection, baseQuery string, params SearchParams) ([]map[string]interface{}, error) {
    // Replace the wildcard placeholders with actual values
    finalQuery := strings.ReplaceAll(baseQuery, "testtype=*", fmt.Sprintf("testtype=%s", params.authType))
    finalQuery = strings.ReplaceAll(finalQuery, "testtarget=*", fmt.Sprintf("testtarget=%s", params.target))
    
    // If the value is "all", replace it back with wildcard
    if params.authType == "all" {
        finalQuery = strings.ReplaceAll(finalQuery, "testtype=all", "testtype=*")
    }
    if params.target == "all" {
        finalQuery = strings.ReplaceAll(finalQuery, "testtarget=all", "testtarget=*")
    }
    
    searchOptions := splunk.SearchOptions{
        MaxCount:        100,
        UseEarliestTime: true,
        EarliestTime:    time.Now().Add(-60 * time.Minute), // Changed to 60 minutes
        UseLatestTime:   true,
        LatestTime:      time.Now(),
}

    return conn.Search(finalQuery, searchOptions)
}

func createSearchCommand(name, description, searchQuery string, isStats bool) *cobra.Command {
    params := SearchParams{}
    
    cmd := &cobra.Command{
        Use:   name,
        Short: description,
        Run: func(cmd *cobra.Command, args []string) {
            fmt.Printf("Executing %s query...\n", name)
            if params.authType != "all" || params.target != "all" {
                fmt.Printf("Using filters - Type: %s, Target: %s\n", params.authType, params.target)
            }
            
            recs, err := executeSearch(globalSplunkConn, searchQuery, params)
            if err != nil {
                fmt.Printf("Error executing query: %v\n", err)
                return
            }
            
            fmt.Printf("\n%s Results:\n", strings.Title(name))
            if isStats {
                formatStatsResults(recs)
            } else {
                formatResultsTable(recs)
            }
        },
    }

    cmd.Flags().StringVar(&params.authType, "type", "all", "Authentication type (ldap/ntlm/dns/all)")
    cmd.Flags().StringVar(&params.target, "target", "all", "Target user/group")

    cmd.PreRunE = func(cmd *cobra.Command, args []string) error {
        if params.authType != "all" {
            validTypes := map[string]bool{
                "ldap": true,
                "ntlm": true,
                "dns":  true,
            }
            if !validTypes[params.authType] {
                return fmt.Errorf("invalid type %q: must be one of ldap, ntlm, dns, or all", params.authType)
            }
        }
        return nil
    }

    return cmd
}

func main() {
    fmt.Println(`
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║     ░██████╗██████╗░██╗░░░░░██╗░░░██╗███╗░░██╗██╗░░██╗     ║
    ║     ██╔════╝██╔══██╗██║░░░░░██║░░░██║████╗░██║██║░██╔╝     ║
    ║     ╚█████╗░██████╔╝██║░░░░░██║░░░██║██╔██╗██║█████═╝      ║
    ║     ░╚═══██╗██╔═══╝░██║░░░░░██║░░░██║██║╚████║██╔═██╗      ║
    ║     ██████╔╝██║░░░░░███████╗╚██████╔╝██║░╚███║██║░╚██╗     ║
    ║     ╚═════╝░╚═╝░░░░░╚══════╝░╚═════╝░╚═╝░░╚══╝╚═╝░░╚═╝     ║
    ║                                                              ║
    ║                      𝑪 𝑳 𝑰                                   ║
    ╠══════════════════════════════════════════════════════════════╣
    ║                     For Probes                               ║
    ╚══════════════════════════════════════════════════════════════╝
`)

    // Version and info
    fmt.Println("    Version: 1.0.0")
    fmt.Println("    Type 'help' for available commands or 'exit' to quit")
    fmt.Println("    --------------------------------------------------------")
    fmt.Println()

    fmt.Print("Enter Splunk username: ")
    reader := bufio.NewReader(os.Stdin)
    username, _ := reader.ReadString('\n')
    username = strings.TrimSpace(username)

    fmt.Print("Enter Splunk password: ")
    bytePassword, _ := term.ReadPassword(int(os.Stdin.Fd()))
    fmt.Println()
    password := strings.TrimSpace(string(bytePassword))

    globalSplunkConn = splunk.Connection{
        Host:     "https://splunk-server:8089",
        AuthType: "basic",
        Username: username,
        Password: password,
    }

    _, err := executeSearch(globalSplunkConn, "search index=_internal | head 1", SearchParams{})
    if err != nil {
        fmt.Printf("Failed to connect to Splunk: %v\n", err)
        os.Exit(1)
    }
    fmt.Println("Successfully authenticated to Splunk!")

    rootCmd := &cobra.Command{
        Use:   "splunk-cli",
        Short: "CLI to interact with Splunk using go-splunk-rest",
    }

    // Regular searches
    searches := map[string]string{
        "query-user": "search index=_internal sourcetype=user_data | stats count by user, type",
        "query-group": "search index=_internal sourcetype=group_data | stats count by group, type",
        "query-failures": "search index=_internal sourcetype=error_logs | stats count by error, type",
    }

    // Add regular search commands
    for name, query := range searches {
        cmd := createSearchCommand(name, fmt.Sprintf("Query %s data", strings.TrimPrefix(name, "query-")), query, false)
        rootCmd.AddCommand(cmd)
    }

    // Add stats command
    statsQuery := "search index=_internal sourcetype=auth_data | stats count by status"
    statsCmd := createSearchCommand("query-stats", "Show authentication statistics", statsQuery, true)
    rootCmd.AddCommand(statsCmd)

    // Add help command
    helpCmd := &cobra.Command{
        Use:   "help",
        Short: "Display help information",
        Run: func(cmd *cobra.Command, args []string) {
            fmt.Println("\nAvailable Commands:")
            fmt.Println("  query-user      Query user data")
            fmt.Println("  query-group     Query group data")
            fmt.Println("  query-failures  Query failure data")
            fmt.Println("  query-stats     Show authentication statistics")
            fmt.Println("  help            Display this help message")
            fmt.Println("  exit            Exit the program")
            fmt.Println("\nFlags:")
            fmt.Println("  --type string    Authentication type (ldap/ntlm/dns/all) (default \"all\")")
            fmt.Println("  --target string  Target user/group (default \"all\")")
        },
    }
    rootCmd.AddCommand(helpCmd)

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

        // Split the input properly handling quoted arguments
        args := parseCommandLine(input)
        
        // Reset root command for each iteration
        rootCmd.ResetFlags()
        rootCmd.ResetCommands()
        
        // Re-add all commands
        for name, query := range searches {
            cmd := createSearchCommand(name, fmt.Sprintf("Query %s data", strings.TrimPrefix(name, "query-")), query, false)
            rootCmd.AddCommand(cmd)
        }
        rootCmd.AddCommand(statsCmd)
        rootCmd.AddCommand(helpCmd)

        // Execute the command with arguments
        rootCmd.SetArgs(args)
        if err := rootCmd.Execute(); err != nil {
            fmt.Printf("Error: %v\n", err)
        }
    }
}

// Add this new function to properly parse command line arguments
func parseCommandLine(input string) []string {
    var args []string
    var currentArg strings.Builder
    inQuotes := false
    
    for _, char := range input {
        switch char {
        case '"':
            inQuotes = !inQuotes
        case ' ':
            if !inQuotes {
                if currentArg.Len() > 0 {
                    args = append(args, currentArg.String())
                    currentArg.Reset()
                }
            } else {
                currentArg.WriteRune(char)
            }
        default:
            currentArg.WriteRune(char)
        }
    }
    
    if currentArg.Len() > 0 {
        args = append(args, currentArg.String())
    }
    
    return args
}
