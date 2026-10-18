<!-- 809-baseline-r2: Copilot CLI, model auto -> gpt-5.6-luna, 1.9 AI credits, session a1417ed3-2f4d-4281-adc8-4cba304a2154 -->
### test/integration/cassandra_client_test.go:86

`ConnectionHost` returns only the container hostname, not the host-mapped CQL port. Since Cassandra's exposed port is dynamically mapped by Testcontainers, passing this value to `gocql.NewCluster` makes the client fall back to port `9042` on the host, which will generally fail to connect. Retrieve `ConnectionPort` as well and pass `host:port` (or use the module's connection-string helper).
