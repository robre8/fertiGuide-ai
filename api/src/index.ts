import { ApolloServer } from '@apollo/server';
import { expressMiddleware } from '@apollo/server/express4';
import { typeDefs } from './schema';
import { resolvers } from './resolvers';
import express from 'express';
import cors from 'cors';
import 'dotenv/config';

async function main() {
  const app = express();
  const server = new ApolloServer({ typeDefs, resolvers });
  await server.start();

  app.use(
    '/',
    cors({
      origin: [
        'http://localhost:3000',
        'https://ferti-guide-ai.vercel.app',
        /\.vercel\.app$/
      ],
      credentials: true
    }),
    express.json(),
    expressMiddleware(server)
  );

  const PORT = parseInt(process.env.PORT || '4000');
  app.listen(PORT, () => {
    console.log(`🚀 GraphQL API ready at http://localhost:${PORT}`);
  });
}

main();
