<!-- 809-guided-r1: Copilot CLI, model auto -> copilot-search-a, gpt-5.6-luna, 2.12 AI credits, session a80e0a47-0d6b-40b5-ace9-0658ee535dde -->
### test/integration/cassandra_client_test.go:86
`ConnectionHost` returns only the Docker host, not the mapped Cassandra port. Since Testcontainers maps port `9042` to a dynamically allocated host port, passing this value to `gocql.NewCluster` makes the client try `host:9042` and the integration test cannot connect. Use the Cassandra module's connection string or append the mapped `9042/tcp` port.
