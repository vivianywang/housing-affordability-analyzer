
import axios from "axios";

const API_BASE = "https://housing-affordability-analyzer.onrender.com";

export class BackendUnreachableError extends Error {
  constructor() {
    super("Could not reach the Flask backend.");
    this.name = "BackendUnreachableError";
  }
}

const client = axios.create({ baseURL: API_BASE });

async function request(config) {
  try {
    const response = await client(config);
    return response.data;
  } catch (err) {
    if (!err.response) throw new BackendUnreachableError();
    throw new Error(err.response.data?.error || `Request failed (${err.response.status})`);
  }
}

export const api = {
  getCities: () => request({ url: "/cities" }),
  getCity: (cityName) => request({ url: `/city/${encodeURIComponent(cityName)}` }),
  getSummary: () => request({ url: "/summary" }),
  getMetadata: () => request({ url: "/metadata" }),
  getRanking: () => request({ url: "/ranking" }),
  calculate: (payload) => request({ url: "/calculate", method: "post", data: payload }),
};