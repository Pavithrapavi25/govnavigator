// ============================================================
// GovNavigator API Service
// ============================================================

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

// ============================================================
// GENERIC API HELPER
// ============================================================

async function apiRequest(endpoint, options = {}) {
    try {
        // Get the latest JWT token for every request
        const token = localStorage.getItem(
            "govnavigator_token"
        );

        const response = await fetch(
            `${API_BASE_URL}${endpoint}`,
            {
                ...options,

                headers: {
                    "Content-Type": "application/json",

                    ...(token
                        ? {
                            Authorization: `Bearer ${token}`,
                        }
                        : {}),

                    ...(options.headers || {}),
                },
            }
        );

        if (!response.ok) {
            let errorMessage =
                `API Error: ${response.status} ${response.statusText}`;

            try {
                const errorData = await response.json();

                if (errorData.detail) {
                    errorMessage +=
                        ` - ${errorData.detail}`;
                }
            } catch {
                // Ignore JSON parsing errors
            }

            // If JWT has expired/failed, remove stored authentication
            if (response.status === 401) {
                localStorage.removeItem(
                    "govnavigator_token"
                );

                localStorage.removeItem(
                    "govnavigator_user"
                );
            }

            throw new Error(errorMessage);
        }

        return await response.json();

    } catch (error) {
        console.error(
            "GovNavigator API Error:",
            error
        );

        throw error;
    }
}


// ============================================================
// AUTHENTICATION
// ============================================================

export async function registerUser(
    name,
    email,
    password
) {
    return apiRequest(
        "/api/auth/register",
        {
            method: "POST",

            body: JSON.stringify({
                name,
                email,
                password,
            }),
        }
    );
}


export async function loginUser(
    email,
    password
) {
    const data = await apiRequest(
        "/api/auth/login",
        {
            method: "POST",

            body: JSON.stringify({
                email,
                password,
            }),
        }
    );

    // Save JWT token
    if (data.token) {
        localStorage.setItem(
            "govnavigator_token",
            data.token
        );
    }

    // Save user information
    if (data.user) {
        localStorage.setItem(
            "govnavigator_user",
            JSON.stringify(data.user)
        );
    }

    return data;
}


export function logoutUser() {
    localStorage.removeItem(
        "govnavigator_token"
    );

    localStorage.removeItem(
        "govnavigator_user"
    );
}


export function getStoredUser() {
    const user = localStorage.getItem(
        "govnavigator_user"
    );

    if (!user) {
        return null;
    }

    try {
        return JSON.parse(user);
    } catch {
        return null;
    }
}


export function isAuthenticated() {
    return Boolean(
        localStorage.getItem(
            "govnavigator_token"
        )
    );
}


// ============================================================
// HEALTH CHECK
// ============================================================

export async function getBackendStatus() {
    return apiRequest("/");
}


// ============================================================
// DATABASE
// ============================================================

export async function getDatabaseStatus() {
    return apiRequest(
        "/api/database"
    );
}


// ============================================================
// STATES
// ============================================================

export async function getStates() {
    return apiRequest(
        "/api/states"
    );
}


export async function getState(stateId) {
    return apiRequest(
        `/api/states/${stateId}`
    );
}


// ============================================================
// SERVICES
// ============================================================

export async function getServices() {
    return apiRequest(
        "/api/services"
    );
}


export async function getService(serviceId) {
    return apiRequest(
        `/api/services/${serviceId}`
    );
}


export async function getServicesByState(
    stateId
) {
    return apiRequest(
        `/api/services/state/${stateId}`
    );
}


// ============================================================
// SMART SEARCH
// ============================================================

export async function smartSearch(
    query,
    stateId = null
) {
    let endpoint =
        `/api/search?q=${encodeURIComponent(query)}`;

    if (
        stateId !== null &&
        stateId !== undefined &&
        stateId !== ""
    ) {
        endpoint +=
            `&state_id=${encodeURIComponent(stateId)}`;
    }

    return apiRequest(endpoint);
}


// ============================================================
// SEARCH HISTORY
// ============================================================

export async function createSearchHistory(
    searchData
) {
    return apiRequest(
        "/api/search-history",
        {
            method: "POST",

            body: JSON.stringify(
                searchData
            ),
        }
    );
}


export async function getSearchHistory() {
    return apiRequest(
        "/api/search-history"
    );
}


// Delete one search-history item
export async function deleteSearchHistory(
    historyId
) {
    return apiRequest(
        `/api/search-history/${historyId}`,
        {
            method: "DELETE",
        }
    );
}


// Clear all search history for current user
export async function clearSearchHistory() {
    return apiRequest(
        "/api/search-history",
        {
            method: "DELETE",
        }
    );
}


// ============================================================
// FAVORITES / SAVED SERVICES
// ============================================================

export async function getFavorites() {
    return apiRequest(
        "/api/favorites"
    );
}


export async function addFavorite(
    serviceId
) {
    return apiRequest(
        "/api/favorites",
        {
            method: "POST",

            body: JSON.stringify({
                service_id: serviceId,
            }),
        }
    );
}


export async function removeFavorite(
    serviceId
) {
    return apiRequest(
        `/api/favorites/${serviceId}`,
        {
            method: "DELETE",
        }
    );
}


export async function checkFavorite(
    serviceId
) {
    return apiRequest(
        `/api/favorites/${serviceId}`
    );
}


// ============================================================
// CHAT
// ============================================================

export async function sendChatMessage(
    message,
    sessionId
) {
    return apiRequest(
        "/api/chat",
        {
            method: "POST",

            body: JSON.stringify({
                message,
                session_id: sessionId,
            }),
        }
    );
}


// ============================================================
// CHAT HISTORY
// ============================================================

export async function getChatHistory() {
    return apiRequest(
        "/api/chat-history"
    );
}


export async function getSessionChatHistory(
    sessionId
) {
    return apiRequest(
        `/api/chat-history/${sessionId}`
    );
}


// ============================================================
// SESSION
// ============================================================

export async function createSession(
    sessionData = {}
) {
    return apiRequest(
        "/api/session",
        {
            method: "POST",

            body: JSON.stringify(
                sessionData
            ),
        }
    );
}


export async function getSession(
    sessionId
) {
    return apiRequest(
        `/api/session/${sessionId}`
    );
}


// ============================================================
// ANALYTICS
// ============================================================

export async function getSearchAnalytics() {
    return apiRequest(
        "/api/analytics/search-summary"
    );
}


// ============================================================
// DEFAULT EXPORT
// ============================================================

const api = {

    // Authentication
    registerUser,
    loginUser,
    logoutUser,
    getStoredUser,
    isAuthenticated,

    // Health
    getBackendStatus,

    // Database
    getDatabaseStatus,

    // States
    getStates,
    getState,

    // Services
    getServices,
    getService,
    getServicesByState,

    // Smart Search
    smartSearch,

    // Search History
    createSearchHistory,
    getSearchHistory,
    deleteSearchHistory,
    clearSearchHistory,

    // Favorites
    getFavorites,
    addFavorite,
    removeFavorite,
    checkFavorite,

    // Chat
    sendChatMessage,

    // Chat History
    getChatHistory,
    getSessionChatHistory,

    // Session
    createSession,
    getSession,

    // Analytics
    getSearchAnalytics,

};

export default api;