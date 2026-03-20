import { api } from "./api";
import { AuthTokens, LoginCredentials, User, CampaignMembership } from "@/types";

interface LoginResponse {
  user: User;
  tokens: AuthTokens;
}

export async function login(credentials: LoginCredentials): Promise<AuthTokens> {
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(credentials),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Login failed" }));
    throw new Error(error.detail);
  }

  const data: LoginResponse = await response.json();
  api.setToken(data.tokens.access_token);
  api.setRefreshToken(data.tokens.refresh_token);
  return data.tokens;
}

export async function logout(): Promise<void> {
  try {
    await api.post("/auth/logout");
  } finally {
    api.clearTokens();
  }
}

export async function getCurrentUser(): Promise<User> {
  return api.get<User>("/auth/me");
}

export async function getMyCampaigns(): Promise<CampaignMembership[]> {
  return api.get<CampaignMembership[]>("/campaigns/memberships/me");
}

export function isAuthenticated(): boolean {
  if (typeof window === "undefined") return false;
  return !!localStorage.getItem("access_token");
}
