from oauth2client import file, client, tools

scope = ["https://www.googleapis.com/auth/spreadsheets"]
store = file.Storage("token.pickle")
creds = store.get()

if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets("credentials.json", scope)
    creds = tools.run_flow(flow, store)

print("Token created! token.pickle saved.")
