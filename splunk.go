package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"

	"github.com/pvik/go-splunk-rest"
	"github.com/spf13/cobra"
	"golang.org/x/term"
)

func main() {
	var username, password string
	var splunkClient *splunk.Client

	authenticate := func() {
		fmt.Print("Enter Splunk username: ")
		reader := bufio.NewReader(os.Stdin)
		username, _ = reader.ReadString('\n')
		username = strings.TrimSpace(username)

		fmt.Print("Enter Splunk password: ")
		bytePassword, _ := term.ReadPassword(int(os.Stdin.Fd()))
		fmt.Println()
		password = strings.TrimSpace(string(bytePassword))

		// Create Splunk client session
		var err error
		splunkClient, err = splunk.NewClient(username, password, "https://splunk-server:8089")
		if err != nil {
			fmt.Printf("Failed to create Splunk client: %v\n", err)
			os.Exit(1)
		}
		fmt.Println("Successfully authenticated to Splunk!")
	}

	rootCmd := &cobra.Command{
		Use:   "splunk-cli",
		Short: "CLI to interact with Splunk using go-splunk-rest",
		Run: func(cmd *cobra.Command, args []string) {
			fmt.Println("Welcome to Splunk CLI. Type 'help' to see available commands or 'exit' to quit.")
			authenticate()

			for {
				fmt.Print("splunk-cli> ")
				reader := bufio.NewReader(os.Stdin)
				input, _ := reader.ReadString('\n')
				input = strings.TrimSpace(input)

				if input == "exit" {
					fmt.Println("Exiting Splunk CLI. Goodbye!")
					break
				}

				args := strings.Split(input, " ")
				if err := rootCmd.ExecuteContext(cmd.Context(), args...); err != nil {
					fmt.Printf("Error: %v\n", err)
				}
			}
		},
	}

	// Command to query users
	queryUserCmd := &cobra.Command{
		Use:   "query-user",
		Short: "Query user data",
		Run: func(cmd *cobra.Command, args []string) {
			response, err := splunkClient.Query("search index=_internal sourcetype=user_data | stats count by user")
			if err != nil {
				fmt.Printf("Error querying users: %v\n", err)
				return
			}
			fmt.Println("User Query Results:")
			fmt.Println(response)
		},
	}
	rootCmd.AddCommand(queryUserCmd)

	// Command to query groups
	queryGroupCmd := &cobra.Command{
		Use:   "query-group",
		Short: "Query group data",
		Run: func(cmd *cobra.Command, args []string) {
			response, err := splunkClient.Query("search index=_internal sourcetype=group_data | stats count by group")
			if err != nil {
				fmt.Printf("Error querying groups: %v\n", err)
				return
			}
			fmt.Println("Group Query Results:")
			fmt.Println(response)
		},
	}
	rootCmd.AddCommand(queryGroupCmd)

	// Command to query failures
	queryFailuresCmd := &cobra.Command{
		Use:   "query-failures",
		Short: "Query failure data",
		Run: func(cmd *cobra.Command, args []string) {
			response, err := splunkClient.Query("search index=_internal sourcetype=error_logs | stats count by error")
			if err != nil {
				fmt.Printf("Error querying failures: %v\n", err)
				return
			}
			fmt.Println("Failure Query Results:")
			fmt.Println(response)
		},
	}
	rootCmd.AddCommand(queryFailuresCmd)

	// Run the CLI loop
	if err := rootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
