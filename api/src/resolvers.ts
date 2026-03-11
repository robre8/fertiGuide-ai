import axios from 'axios';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export const resolvers = {
  Query: {
    health: async () => {
      try {
        await axios.get(`${BACKEND_URL}/health`);
        return { status: 'ok', backend: 'connected' };
      } catch {
        return { status: 'ok', backend: 'disconnected' };
      }
    }
  },

  Mutation: {
    askAssistant: async (_: unknown, { message }: { message: string }) => {
      const res = await axios.post(`${BACKEND_URL}/chat`, { message });
      return { response: res.data.response };
    }
  }
};
