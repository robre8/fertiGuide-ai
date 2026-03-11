export const typeDefs = `#graphql
  type ChatResponse {
    response: String!
  }

  type HealthStatus {
    status: String!
    backend: String!
  }

  type Query {
    health: HealthStatus!
  }

  type Mutation {
    askAssistant(message: String!): ChatResponse!
  }
`;
