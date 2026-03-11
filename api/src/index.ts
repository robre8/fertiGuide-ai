import { ApolloServer } from '@apollo/server';
import { startStandaloneServer } from '@apollo/server/standalone';
import { typeDefs } from './schema';
import { resolvers } from './resolvers';
import 'dotenv/config';

async function main() {
  const server = new ApolloServer({ typeDefs, resolvers });

  const { url } = await startStandaloneServer(server, {
    listen: { port: parseInt(process.env.PORT || '4000') },
    context: async ({ req }) => {
      return {};
    }
  });

  console.log(`🚀 GraphQL API ready at ${url}`);
}

main();
