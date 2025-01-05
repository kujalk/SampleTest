package main

import (
    "bufio"
    "crypto/tls"
    "fmt"
    "net/http"
    "os"
    "strings"
    "time"

    "github.com/pvik/go-splunk-rest"
    "github.com/spf13/cobra"
    "golang.org/x/term"
)

func main() {
    var splunkConn splunk.Connection

    // Authenticate immediately when program starts
    fmt.Print("Enter Splunk username: ")
    reader := bufio.NewReader(os.Stdin)
    username, _ := reader.ReadString('\n')
    username = strings.TrimSpace(username)

    fmt.Print("Enter Splunk password: ")
    bytePassword, _ := term.ReadPassword(int(os.Stdin.Fd()))
    fmt.Println()
    password := strings.TrimSpace(string(bytePassword))

    // Create custom HTTP client with TLS skip verify
    tr := &http.Transport{
        TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
    }
    httpClient := &http.Client{Transport: tr}

    // Create Splunk connection session
    splunkConn = splunk.Connection{
        Host:       "https://splunk-server:8089",
        AuthType:   "basic",
        Username:   username,
        Password:   password,
        HTTPClient: httpClient,
    }

    fmt.Println("Successfully authenticated to Splunk!")

    rootCmd := &cobra.Command{
        Use:   "splunk-cli",
        Short: "CLI to interact with Splunk using go-splunk-rest",
    }

    // Command to query users
    queryUserCmd := &cobra.Command{
        Use:   "query-user",
        Short: "Query user data",
        Run: func(cmd *cobra.Command, args []string) {
            searchOptions := splunk.SearchOptions{
                MaxCount:        100,
                UseEarliestTime: true,
                EarliestTime:    time.Now().Add(-30 * 24 * time.Hour),
                UseLatestTime:   true,
                LatestTime:      time.Now(),
            }

            recs, err := splunkConn.Search("search index=_internal sourcetype=user_data | stats count by user", searchOptions)
            if err != nil {
                fmt.Printf("Error querying users: %v\n", err)
                return
            }
            fmt.Println("User Query Results:")
            fmt.Println(recs)
        },
    }
    rootCmd.AddCommand(queryUserCmd)

    // Command to query groups
    queryGroupCmd := &cobra.Command{
        Use:   "query-group",
        Short: "Query group data",
        Run: func(cmd *cobra.Command, args []string) {
            searchOptions := splunk.SearchOptions{
                MaxCount:        100,
                UseEarliestTime: true,
                EarliestTime:    time.Now().Add(-30 * 24 * time.Hour),
                UseLatestTime:   true,
                LatestTime:      time.Now(),
            }

            recs, err := splunkConn.Search("search index=_internal sourcetype=group_data | stats count by group", searchOptions)
            if err != nil {
                fmt.Printf("Error querying groups: %v\n", err)
                return
            }
            fmt.Println("Group Query Results:")
            fmt.Println(recs)
        },
    }
    rootCmd.AddCommand(queryGroupCmd)

    // Command to query failures
    queryFailuresCmd := &cobra.Command{
        Use:   "query-failures",
        Short: "Query failure data",
        Run: func(cmd *cobra.Command, args []string) {
            searchOptions := splunk.SearchOptions{
                MaxCount:        100,
                UseEarliestTime: true,
                EarliestTime:    time.Now().Add(-30 * 24 * time.Hour),
                UseLatestTime:   true,
                LatestTime:      time.Now(),
            }

            recs, err := splunkConn.Search("search index=_internal sourcetype=error_logs | stats count by error", searchOptions)
            if err != nil {
                fmt.Printf("Error querying failures: %v\n", err)
                return
            }
            fmt.Println("Failure Query Results:")
            fmt.Println(recs)
        },
    }
    rootCmd.AddCommand(queryFailuresCmd)

    // Main command loop
    for {
        fmt.Print("splunk-cli> ")
        input, _ := reader.ReadString('\n')
        input = strings.TrimSpace(input)

        if input == "exit" {
            fmt.Println("Exiting Splunk CLI. Goodbye!")
            break
        }

        args := strings.Split(input, " ")
        rootCmd.SetArgs(args)
        if err := rootCmd.Execute(); err != nil {
            fmt.Printf("Error: %v\n", err)
        }
    }
}
