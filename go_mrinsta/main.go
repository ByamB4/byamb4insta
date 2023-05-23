package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os"
)

const (
	BaseURL  = "https://api.mrinsta.com/api"
	Password = "p4$$w0rD!"
)

type Account struct {
	Email string `json:"email"`
}

func main() {
	accounts, err := readAccountsFromFile("accounts.json")
	if err != nil {
		fmt.Println("Error reading accounts:", err)
		return
	}
	for _, account := range accounts {
		login(account)
	}
	// printEmails(accounts)
}

func login(account {}Account) (bool, string, string) {
	return false, "", ""
}

func readAccountsFromFile(filename string) ([]Account, error) {
	file, err := os.Open(filename)
	if err != nil {
		return nil, fmt.Errorf("error opening file: %w", err)
	}
	defer file.Close()
	data, err := ioutil.ReadAll(file)
	if err != nil {
		return nil, fmt.Errorf("error reading file: %w", err)
	}
	var accounts []Account
	err = json.Unmarshal(data, &accounts)
	if err != nil {
		return nil, fmt.Errorf("error parsing JSON: %w", err)
	}
	return accounts, nil
}

// func printEmails(accounts []Account) {
// 	for _, account := range accounts {
// 		fmt.Println("Email: ", account.Email)
// 	}
// }
