"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { API_URL } from "./utils";

// =============================================================================
// Types
// =============================================================================

interface User {
  id: string;
  email: string;
  display_name: string | null;
  avatar_url: string | null;
  oauth_provider: string | null;
  is_active: boolean;
  created_at: string;
}

interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

interface RegisterResponse extends AuthTokens {
  user_id: string;
  email: string;
  display_name: string | null;
  seed_phrase: string;
}

interface LoginResponse extends AuthTokens {
  user_id: string;
  email: string;
  display_name: string | null;
}

interface GoogleOAuthResponse {
  user_id: string;
  email: string;
  display_name: string | null;
  avatar_url: string | null;
  is_new_user: boolean;
  seed_phrase: string | null;
  access_token: string;
  refresh_token: string;
  token_type: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (
    email: string,
    password: string,
    displayName?: string
  ) => Promise<RegisterResponse>;
  logout: () => Promise<void>;
  refreshTokens: () => Promise<boolean>;
  getAccessToken: () => string | null;
  getGoogleAuthUrl: () => Promise<string>;
  handleGoogleCallback: (code: string) => Promise<GoogleOAuthResponse>;
}

// =============================================================================
// Context
// =============================================================================

const AuthContext = createContext<AuthContextType | null>(null);

// =============================================================================
// Storage Keys
// =============================================================================

const STORAGE_KEYS = {
  ACCESS_TOKEN: "afas_access_token",
  REFRESH_TOKEN: "afas_refresh_token",
  USER: "afas_user",
} as const;

// =============================================================================
// Provider
// =============================================================================

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load user from localStorage on mount
  useEffect(() => {
    const loadStoredAuth = async () => {
      try {
        const storedUser = localStorage.getItem(STORAGE_KEYS.USER);
        const accessToken = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);

        if (storedUser && accessToken) {
          // Validate token by fetching current user
          const response = await fetch(`${API_URL}/auth/me`, {
            headers: {
              Authorization: `Bearer ${accessToken}`,
            },
          });

          if (response.ok) {
            const userData = await response.json();
            setUser(userData);
          } else if (response.status === 401) {
            // Try to refresh tokens
            const refreshed = await refreshTokensInternal();
            if (!refreshed) {
              clearAuth();
            }
          } else {
            clearAuth();
          }
        }
      } catch (error) {
        console.error("Error loading stored auth:", error);
        clearAuth();
      } finally {
        setIsLoading(false);
      }
    };

    loadStoredAuth();
  }, []);

  const clearAuth = useCallback(() => {
    localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.USER);
    setUser(null);
  }, []);

  const storeTokens = useCallback((tokens: AuthTokens) => {
    localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, tokens.access_token);
    localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, tokens.refresh_token);
  }, []);

  const refreshTokensInternal = async (): Promise<boolean> => {
    try {
      const refreshToken = localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
      if (!refreshToken) return false;

      const response = await fetch(`${API_URL}/auth/refresh`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) return false;

      const tokens: AuthTokens = await response.json();
      storeTokens(tokens);

      // Fetch updated user info
      const userResponse = await fetch(`${API_URL}/auth/me`, {
        headers: {
          Authorization: `Bearer ${tokens.access_token}`,
        },
      });

      if (userResponse.ok) {
        const userData = await userResponse.json();
        setUser(userData);
        localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(userData));
      }

      return true;
    } catch (error) {
      console.error("Token refresh failed:", error);
      return false;
    }
  };

  const login = useCallback(
    async (email: string, password: string): Promise<void> => {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Login failed");
      }

      const data: LoginResponse = await response.json();
      storeTokens(data);

      // Fetch full user info
      const userResponse = await fetch(`${API_URL}/auth/me`, {
        headers: {
          Authorization: `Bearer ${data.access_token}`,
        },
      });

      if (userResponse.ok) {
        const userData = await userResponse.json();
        setUser(userData);
        localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(userData));
      }
    },
    [storeTokens]
  );

  const register = useCallback(
    async (
      email: string,
      password: string,
      displayName?: string
    ): Promise<RegisterResponse> => {
      const response = await fetch(`${API_URL}/auth/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          password,
          display_name: displayName || null,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Registration failed");
      }

      const data: RegisterResponse = await response.json();
      storeTokens(data);

      // Fetch full user info
      const userResponse = await fetch(`${API_URL}/auth/me`, {
        headers: {
          Authorization: `Bearer ${data.access_token}`,
        },
      });

      if (userResponse.ok) {
        const userData = await userResponse.json();
        setUser(userData);
        localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(userData));
      }

      // Return the full response including seed_phrase (shown only once!)
      return data;
    },
    [storeTokens]
  );

  const logout = useCallback(async (): Promise<void> => {
    try {
      const accessToken = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
      const refreshToken = localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);

      if (accessToken && refreshToken) {
        await fetch(`${API_URL}/auth/logout`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
          },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
      }
    } catch (error) {
      console.error("Logout error:", error);
    } finally {
      clearAuth();
    }
  }, [clearAuth]);

  const getAccessToken = useCallback((): string | null => {
    return localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
  }, []);

  const getGoogleAuthUrl = useCallback(async (): Promise<string> => {
    const response = await fetch(`${API_URL}/auth/google/login`);
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to get Google auth URL");
    }
    const data = await response.json();
    return data.auth_url;
  }, []);

  const handleGoogleCallback = useCallback(
    async (code: string): Promise<GoogleOAuthResponse> => {
      const response = await fetch(`${API_URL}/auth/google/callback?code=${encodeURIComponent(code)}`);
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Google authentication failed");
      }

      const data: GoogleOAuthResponse = await response.json();
      storeTokens(data);

      // Fetch full user info
      const userResponse = await fetch(`${API_URL}/auth/me`, {
        headers: {
          Authorization: `Bearer ${data.access_token}`,
        },
      });

      if (userResponse.ok) {
        const userData = await userResponse.json();
        setUser(userData);
        localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(userData));
      }

      return data;
    },
    [storeTokens]
  );

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    refreshTokens: refreshTokensInternal,
    getAccessToken,
    getGoogleAuthUrl,
    handleGoogleCallback,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// =============================================================================
// Hook
// =============================================================================

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

// =============================================================================
// Authenticated API Request Helper
// =============================================================================

export async function authenticatedRequest<T>(
  endpoint: string,
  options?: RequestInit,
  getToken?: () => string | null
): Promise<T> {
  const token = getToken?.() || localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...options?.headers,
  };

  if (token) {
    (headers as Record<string, string>).Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    if (response.status === 401) {
      // Token might be expired, caller should handle refresh
      throw new Error("Unauthorized");
    }
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || `API error: ${response.status}`);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}
