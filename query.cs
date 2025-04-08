using Microsoft.VisualBasic;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.DirectoryServices;
using System.DirectoryServices.AccountManagement;
using System.Linq;
using System.Runtime;
using System.Runtime.InteropServices;
using System.Text.RegularExpressions;

namespace TestARSConsole
{
    class Program
    {
        //You can replace below with the group name you want to test.
        static string groupName = "Windows Authorization Access Group";

        static void Main(string[] args)
        {
            try
            {
                Console.WriteLine("Attempting to connect to Quest Active Roles Server...");
                
                // Adding more complete error handling and diagnostics
                DirectoryEntry ent = null;
                
                try {
                    // Modified connection string with proper credentials and options
                    ent = new DirectoryEntry(
                        "EDMS://mvars.server",  // Server URL
                        @"domain1\e444",        // Username
                        "YourPassword",         // Add proper password here
                        AuthenticationTypes.Secure | AuthenticationTypes.Sealing | AuthenticationTypes.Signing
                    );
                    
                    // Enable more verbose ADSI error information
                    ent.Options.ReferralChasing = ReferralChasingOption.All;
                    ent.RefreshCache();
                    
                    Console.WriteLine("Connection successful.");
                    Console.WriteLine("Connection Account : " + ent.Username);
                    Console.WriteLine("Authentication Type : " + ent.AuthenticationType);
                    
                    // Test if we can read basic properties
                    Console.WriteLine("Testing property access...");
                    object nativeObject = ent.NativeObject;
                    Console.WriteLine("Native object accessed successfully.");
                    
                    // Search for the group with verbose logging
                    Console.WriteLine($"Searching for group: {groupName}");
                    
                    DirectorySearcher dsSearcher = new DirectorySearcher(ent, $"(&(objectClass=group)(cn=" + groupName + "))");
                    dsSearcher.SearchScope = SearchScope.Subtree;
                    dsSearcher.PageSize = 1000;  // Improve search performance
                    dsSearcher.CacheResults = false;  // Don't cache to ensure fresh results
                    
                    Console.WriteLine("Search initiated with filter: " + dsSearcher.Filter);
                    SearchResult searchResult = dsSearcher.FindOne();
                    
                    if (searchResult == null)
                    {
                        Console.WriteLine("No results found.");
                    }
                    else
                    {
                        Console.WriteLine("Result found: " + searchResult.Path);
                        DirectoryEntry groupObj = searchResult.GetDirectoryEntry();
                        
                        try {
                            PropertyValueCollection members = groupObj.Properties["member"];
                            Console.WriteLine("Group Members count : " + members.Count);
                            
                            // Optional: Display some group members
                            if (members.Count > 0)
                            {
                                Console.WriteLine("First few members:");
                                int displayCount = Math.Min(5, members.Count);
                                for (int i = 0; i < displayCount; i++)
                                {
                                    Console.WriteLine($"  - {members[i]}");
                                }
                            }
                        }
                        catch (Exception memberEx)
                        {
                            Console.WriteLine("Error accessing members: " + memberEx.Message);
                        }
                    }
                }
                catch (COMException comEx)
                {
                    Console.WriteLine($"COM Exception occurred: 0x{comEx.ErrorCode:X8}");
                    Console.WriteLine($"Error Message: {comEx.Message}");
                    Console.WriteLine($"Stack Trace: {comEx.StackTrace}");
                    
                    // Special handling for 80005000 error
                    if (comEx.ErrorCode == unchecked((int)0x80005000))
                    {
                        Console.WriteLine("\nERROR 80005000 TROUBLESHOOTING SUGGESTIONS:");
                        Console.WriteLine("1. Verify the Active Roles Server URL is correct (EDMS://mvars.server)");
                        Console.WriteLine("2. Ensure the Active Roles Management Service is running on the target server");
                        Console.WriteLine("3. Check if the credentials have permissions to connect to ARS");
                        Console.WriteLine("4. Verify network connectivity (no firewalls blocking communication)");
                        Console.WriteLine("5. Check if Active Roles client components are properly installed");
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine("Error: " + ex.Message + "\n" + ex.StackTrace);
                    
                    if (ex.InnerException != null)
                    {
                        Console.WriteLine("\nInner Exception:");
                        Console.WriteLine("Error: " + ex.InnerException.Message + "\n" + ex.InnerException.StackTrace);
                    }
                }
                finally
                {
                    if (ent != null)
                    {
                        try
                        {
                            ent.Close();
                            ent.Dispose();
                        }
                        catch { /* Ignore cleanup errors */ }
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine("Unhandled Error: " + ex.Message + "\n" + ex.StackTrace);
            }
            
            Console.WriteLine("\nPress any key to exit...");
            Console.ReadKey();
        }
    }
}
