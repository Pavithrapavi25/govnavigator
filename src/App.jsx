import { useState, useRef } from "react";
import { useEffect } from "react";

import {
  getBackendStatus,
  getStates,
  getServices,
  getService,
  sendChatMessage,
  createSession,
  getSession,
  smartSearch,
  getSearchAnalytics,
  getSessionChatHistory,
  registerUser,
  loginUser,
  logoutUser,
  getStoredUser,
  isAuthenticated,
  getSearchHistory,
  deleteSearchHistory,
  clearSearchHistory,
  getFavorites,
  addFavorite,
  removeFavorite,

} from "./services/api";

import "./App.css";

/*
============================================================
GOVNAVIGATOR
React Frontend
============================================================
*/

/* ============================================================
   GOVNAVIGATOR UI SOUND EFFECTS
   Uses the browser Web Audio API - no external audio files.
   ============================================================ */

let govNavigatorAudioContext = null;

const playUiSound = (type = "click") => {
  try {
    const AudioContextClass =
      window.AudioContext || window.webkitAudioContext;

    if (!AudioContextClass) return;

    if (!govNavigatorAudioContext) {
      govNavigatorAudioContext = new AudioContextClass();
    }

    if (govNavigatorAudioContext.state === "suspended") {
      govNavigatorAudioContext.resume();
    }

    const presets = {
      click: {
        frequency: 520,
        duration: 0.055,
        volume: 0.025,
        wave: "sine",
      },
      success: {
        frequency: 760,
        duration: 0.13,
        volume: 0.04,
        wave: "sine",
      },
      delete: {
        frequency: 230,
        duration: 0.10,
        volume: 0.035,
        wave: "triangle",
      },
      favorite: {
        frequency: 680,
        duration: 0.11,
        volume: 0.035,
        wave: "sine",
      },
      message: {
        frequency: 650,
        duration: 0.09,
        volume: 0.03,
        wave: "sine",
      },
      error: {
        frequency: 180,
        duration: 0.12,
        volume: 0.025,
        wave: "triangle",
      },
    };

    const preset = presets[type] || presets.click;
    const ctx = govNavigatorAudioContext;
    const oscillator = ctx.createOscillator();
    const gain = ctx.createGain();

    oscillator.type = preset.wave;
    oscillator.frequency.setValueAtTime(
      preset.frequency,
      ctx.currentTime
    );

    gain.gain.setValueAtTime(
      preset.volume,
      ctx.currentTime
    );

    gain.gain.exponentialRampToValueAtTime(
      0.001,
      ctx.currentTime + preset.duration
    );

    oscillator.connect(gain);
    gain.connect(ctx.destination);

    oscillator.start();
    oscillator.stop(ctx.currentTime + preset.duration);
  } catch (error) {
    // Sound must never break the application.
    console.debug("UI sound unavailable:", error);
  }
};

function App() {
  const [soundEnabled, setSoundEnabled] = useState(() => {
    const stored = localStorage.getItem("govnavigator_sound_enabled");
    return stored !== "false";
  });

  const soundEnabledRef = useRef(soundEnabled);

  useEffect(() => {
    soundEnabledRef.current = soundEnabled;
    localStorage.setItem(
      "govnavigator_sound_enabled",
      String(soundEnabled)
    );
  }, [soundEnabled]);

  useEffect(() => {
    const handleUiClick = (event) => {
      if (!soundEnabledRef.current) return;

      const button = event.target.closest("button");
      const link = event.target.closest("a");

      if (!button && !link) return;
      if (button?.disabled) return;

      const text = (
        button?.innerText ||
        button?.getAttribute("aria-label") ||
        button?.getAttribute("title") ||
        ""
      ).toLowerCase();

      let soundType = "click";

      if (
        text.includes("delete") ||
        text.includes("clear all") ||
        text.includes("remove")
      ) {
        soundType = "delete";
      } else if (
        text.includes("favorite") ||
        text.includes("save") ||
        text.includes("saved")
      ) {
        soundType = "favorite";
      } else if (
        text.includes("login") ||
        text.includes("register") ||
        text.includes("submit")
      ) {
        soundType = "success";
      }

      playUiSound(soundType);
    };

    document.addEventListener("click", handleUiClick, true);

    return () => {
      document.removeEventListener("click", handleUiClick, true);
    };
  }, []);
  /* ========================================================
     STATE
  ======================================================== */

  const [search, setSearch] = useState("");
  const [selectedService, setSelectedService] = useState(null);
  const [showGuide, setShowGuide] = useState(false);
  const [searchPerformed, setSearchPerformed] = useState(false);
  const [matchScore, setMatchScore] = useState(0);

  const [selectedState, setSelectedState] = useState("");

  // Data loaded from FastAPI + SQLite
  const [dbStates, setDbStates] = useState([]);
  const [dbServices, setDbServices] = useState([]);

  const [showAI, setShowAI] = useState(false);
  const [aiInput, setAiInput] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [sessionId, setSessionId] = useState("");
  const [analytics, setAnalytics] = useState(null);
const [analyticsLoading, setAnalyticsLoading] = useState(false);
const [analyticsError, setAnalyticsError] = useState("");

  // ============================================================
  // AUTHENTICATION
  // ============================================================

  const [currentUser, setCurrentUser] = useState(() => getStoredUser());
  const [showAuth, setShowAuth] = useState(false);
  const [authMode, setAuthMode] = useState("login");
  const [authName, setAuthName] = useState("");
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [showAuthPassword, setShowAuthPassword] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState("");
  const [authSuccess, setAuthSuccess] = useState("");
  const [searchHistory, setSearchHistory] = useState([]);
const [showSearchHistory, setShowSearchHistory] = useState(false);
const [historyLoading, setHistoryLoading] = useState(false);
const [historyError, setHistoryError] = useState("");

  // ============================================================
  // FAVORITES / SAVED SERVICES
  // ============================================================

  const [favorites, setFavorites] = useState([]);
  const [favoritesLoading, setFavoritesLoading] = useState(false);
  const [favoriteLoadingId, setFavoriteLoadingId] = useState(null);
  const [showFavorites, setShowFavorites] = useState(false);
  const [favoritesError, setFavoritesError] = useState("");

  const openLogin = () => {
    setAuthMode("login");
    setAuthError("");
    setAuthSuccess("");
    setAuthPassword("");
    setShowAuthPassword(false);
    setShowAuth(true);
  };

  const openRegister = () => {
    setAuthMode("register");
    setAuthError("");
    setAuthSuccess("");
    setAuthPassword("");
    setShowAuthPassword(false);
    setShowAuth(true);
  };

  const closeAuth = () => {
    if (authLoading) return;
    setShowAuth(false);
    setAuthError("");
    setAuthSuccess("");
  };

  const handleAuthSubmit = async (event) => {
    event.preventDefault();

    setAuthError("");
    setAuthSuccess("");

    const name = authName.trim();
    const email = authEmail.trim().toLowerCase();
    const password = authPassword;

    if (authMode === "register" && !name) {
      setAuthError("Please enter your name.");
      return;
    }

    if (!email) {
      setAuthError("Please enter your email.");
      return;
    }

    if (!password) {
      setAuthError("Please enter your password.");
      return;
    }

    if (authMode === "register" && password.length < 8) {
      setAuthError("Password must be at least 8 characters.");
      return;
    }

    try {
      setAuthLoading(true);

      if (authMode === "register") {
        await registerUser(name, email, password);
        setAuthSuccess("Registration successful. You can now log in.");
        setAuthMode("login");
        setAuthPassword("");
        setShowAuthPassword(false);
      } else {
        const data = await loginUser(email, password);

        if (data.user) {
          setCurrentUser(data.user);
        }
        await loadSearchHistory();

        setAuthSuccess("Login successful.");
        setAuthName("");
        setAuthEmail("");
        setAuthPassword("");

        setTimeout(() => {
          setShowAuth(false);
          loadAnalytics();
        }, 500);
      }
    } catch (error) {
      console.error("Authentication failed:", error);
      const message = error?.message || "Authentication failed. Please try again.";
      setAuthError(
        message.replace(/^API Error:\s*\d+\s*[^-]*-\s*/, "")
      );
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = () => {
    logoutUser();
    setCurrentUser(null);
    setShowAuth(false);
    setAuthMode("login");
    setAuthName("");
    setAuthEmail("");
    setAuthPassword("");
    setShowAuthPassword(false);
    setAuthError("");
    setAuthSuccess("");
    setSearchPerformed(false);
    setSelectedService(null);
    setShowGuide(false);
    setFavorites([]);
    setShowFavorites(false);
    setFavoritesError("");
    setMessages([
      {
        role: "assistant",
        content:
          "Namaste! 🇮🇳 I'm GovNavigator AI. Tell me what government service you need and I'll help you understand the possible service, documents and next steps.",
      },
    ]);
  };

  const getDatabaseServiceId = (service) => {
    if (!service) return null;

    const directId = Number(service.id);
    if (Number.isInteger(directId) && directId > 0) {
      return directId;
    }

    const serviceName = service.name?.trim().toLowerCase();
    if (!serviceName) return null;

    const match = dbServices.find(
      (item) => item.name?.trim().toLowerCase() === serviceName
    );

    const databaseId = Number(match?.id);
    return Number.isInteger(databaseId) && databaseId > 0
      ? databaseId
      : null;
  };

  // Always use the actual government-service database ID when working
  // with saved services. This keeps the frontend compatible with both
  // { service_id: 12 } and older { id: 12 } favorite responses.
  const getFavoriteServiceId = (favorite) => {
    if (!favorite) return null;

    const serviceId = Number(
      favorite.service_id ?? favorite.serviceId ?? favorite.id
    );

    return Number.isInteger(serviceId) && serviceId > 0
      ? serviceId
      : null;
  };

  const loadFavorites = async () => {
    if (!currentUser || !isAuthenticated()) {
      setFavorites([]);
      setFavoritesError("");
      return;
    }

    try {
      setFavoritesLoading(true);
      setFavoritesError("");

      const data = await getFavorites();
      setFavorites(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("Failed to load favorites:", error);
      setFavoritesError(
        error?.message || "Unable to load saved services."
      );
    } finally {
      setFavoritesLoading(false);
    }
  };

  const isServiceFavorite = (service) => {
    const serviceId = getDatabaseServiceId(service);
    if (!serviceId) return false;

    return favorites.some(
      (favorite) => 
        getFavoriteServiceId(favorite) === serviceId
      );
  };

  const toggleFavorite = async (service) => {
    if (!service || service.id === "not-found") return;

    if (!currentUser || !isAuthenticated()) {
      openLogin();
      return;
    }

    const serviceId = getDatabaseServiceId(service);

    if (!serviceId) {
      setFavoritesError(
        "This service is not available in the government services database yet."
      );
      return;
    }

    try {
      setFavoriteLoadingId(serviceId);
      setFavoritesError("");

      if (isServiceFavorite(service)) {
        await removeFavorite(serviceId);
      } else {
        await addFavorite(serviceId);
      }

      await loadFavorites();
    } catch (error) {
      console.error("Failed to update favorite:", error);
      setFavoritesError(
        error?.message || "Unable to update saved service."
      );
    } finally {
      setFavoriteLoadingId(null);
    }
  };

  useEffect(() => {
    if (currentUser && isAuthenticated()) {
      loadFavorites();
    } else {
      setFavorites([]);
      setShowFavorites(false);
    }
  }, [currentUser]);

  const requireLoginForSearch = () => {
    if (isAuthenticated() && currentUser) {
      return true;
    }

    setAuthMode("login");
    setAuthError("Please log in or register before using Smart Search.");
    setAuthSuccess("");
    setShowAuth(true);
    return false;
  };

  const loadAnalytics = async () => {
  try {
    setAnalyticsLoading(true);
    setAnalyticsError("");

    const data = await getSearchAnalytics();

    setAnalytics(data);

  } catch (error) {
    console.error(
      "Failed to load search analytics:",
      error
    );

    setAnalyticsError(
      "Unable to load search analytics."
    );

  } finally {
    setAnalyticsLoading(false);
  }
};
  const loadSearchHistory = async () => {
  if (!isAuthenticated()) {
    setSearchHistory([]);
    return;
  }

  try {
    setHistoryLoading(true);
    setHistoryError("");

    const history = await getSearchHistory();

    setSearchHistory(
      Array.isArray(history) ? history : []
    );
  } catch (error) {
    console.error(
      "Failed to load search history:",
      error
    );

    setHistoryError(
      "Unable to load your search history."
    );
  } finally {
    setHistoryLoading(false);
  }
};

  const handleDeleteSearchHistory = async (historyId) => {
    if (!historyId || historyLoading) return;
    if (!window.confirm("Delete this search from your history?")) return;

    try {
      setHistoryError("");
      await deleteSearchHistory(historyId);
      setSearchHistory((previous) =>
        previous.filter((item) => Number(item.id) !== Number(historyId))
      );
    } catch (error) {
      console.error("Failed to delete search history:", error);
      setHistoryError(error?.message || "Unable to delete this search.");
    }
  };

  const handleClearSearchHistory = async () => {
    if (historyLoading || searchHistory.length === 0) return;
    if (!window.confirm("Clear all of your search history? This cannot be undone.")) return;

    try {
      setHistoryLoading(true);
      setHistoryError("");
      await clearSearchHistory();
      setSearchHistory([]);
    } catch (error) {
      console.error("Failed to clear search history:", error);
      setHistoryError(error?.message || "Unable to clear your search history.");
    } finally {
      setHistoryLoading(false);
    }
  };

  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Namaste! 🇮🇳 I'm GovNavigator AI. Tell me what government service you need and I'll help you understand the possible service, documents and next steps.",
    },
  ]);
  useEffect(() => {
    getBackendStatus()
      .then((data) => {
        console.log("GovNavigator Backend:", data);
      })
      .catch((error) => {
        console.error("Backend connection failed:", error);
      });
  }, []);
  useEffect(() => {
  loadAnalytics();
}, []);

  // Restore/create a persistent browser session.
  useEffect(() => {
    const initializeSession = async () => {
      try {
        let storedSessionId = localStorage.getItem(
          "govnavigator_session_id"
        );

        if (!storedSessionId) {
          storedSessionId =
            typeof crypto !== "undefined" && crypto.randomUUID
              ? crypto.randomUUID()
              : `session_${Date.now()}_${Math.random()
                  .toString(36)
                  .slice(2, 10)}`;

          localStorage.setItem(
            "govnavigator_session_id",
            storedSessionId
          );
        }

        setSessionId(storedSessionId);

        await createSession({
          session_id: storedSessionId,
        });

        const sessionData = await getSession(storedSessionId);

        console.log("GovNavigator Session:", sessionData);

        if (
          Array.isArray(sessionData.chat_history) &&
          sessionData.chat_history.length > 0
        ) {
          const restoredMessages = [];

          sessionData.chat_history.forEach((chat) => {
            restoredMessages.push({
              role: "user",
              content: chat.user_message,
            });

            restoredMessages.push({
              role: "assistant",
              content: formatAIResponse(chat.ai_response),
            });
          });

          setMessages(restoredMessages);
        }
      } catch (error) {
        console.error("Session initialization failed:", error);
      }
    };

    initializeSession();
  }, []);

  // Load states and services from FastAPI + SQLite.
  // Existing hardcoded frontend data remains as fallback.
  useEffect(() => {
    const loadDatabaseData = async () => {
      try {
        const [statesData, servicesData] = await Promise.all([
          getStates(),
          getServices(),
        ]);

        console.log("SQL States:", statesData);
        console.log("SQL Services:", servicesData);

        setDbStates(Array.isArray(statesData) ? statesData : []);
        setDbServices(Array.isArray(servicesData) ? servicesData : []);
      } catch (error) {
        console.error("Failed to load SQL data:", error);
      }
    };

    loadDatabaseData();
  }, []);

  /* ========================================================
     STATES / UTs
  ======================================================== */

  const states = [
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
    "Andaman and Nicobar Islands",
    "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi",
    "Jammu and Kashmir",
    "Ladakh",
    "Lakshadweep",
    "Puducherry",
  ];

  /* ========================================================
     SERVICES
     EXISTING SERVICES ARE KEPT
     NEW SERVICES ARE ADDED BELOW THEM
  ======================================================== */

  const services = [
    /* ======================================================
       EXISTING SERVICES
    ====================================================== */

    {
      id: "income",
      name: "Income Certificate",
      icon: "💰",
      description:
        "Official proof of an individual's or family's income for eligible government services, scholarships and benefits.",
      keywords: [
        "income",
        "income certificate",
        "salary",
        "salary proof",
        "income proof",
        "family income",
        "annual income",
        "earnings",
        "financial proof",
      ],
      eligibility:
        "Individuals who need official proof of income for a government scheme, scholarship, fee concession, reservation-related benefit or another permitted purpose.",
      documents: [
        "Identity proof",
        "Address / residence proof",
        "Income proof such as salary certificate, salary slips, Form 16 or other applicable records",
        "Self-declaration or affidavit, where required",
        "Additional documents specified by the state authority",
      ],
      steps: [
        "Select your state.",
        "Open the applicable official citizen-service portal.",
        "Select Income Certificate.",
        "Enter the required personal and income details.",
        "Upload the required documents.",
        "Submit the application and save the acknowledgement/reference number.",
      ],
      fees:
        "Fees depend on the state, authority and application channel. Verify the current fee before payment.",
      processingTime:
        "Processing time varies by state and verification requirements.",
      mistakes: [
        "Entering incorrect income information",
        "Uploading unclear documents",
        "Providing outdated address information",
        "Submitting incomplete information",
      ],
    },

    {
      id: "caste",
      name: "Caste / Community Certificate",
      icon: "📜",
      description:
        "Official documentation of caste or community status for eligible government, education and employment purposes.",
      keywords: [
        "caste",
        "caste certificate",
        "community",
        "community certificate",
        "caste proof",
        "sc certificate",
        "st certificate",
        "obc certificate",
        "reservation",
        "social category",
      ],
      eligibility:
        "Eligible applicants who require official caste or community documentation for permitted government, educational or employment purposes.",
      documents: [
        "Identity proof",
        "Residence proof",
        "Existing caste/community records, where available",
        "Parent or family certificate, where applicable",
        "School records or other supporting evidence, where required",
        "Affidavit/declaration, where required",
      ],
      steps: [
        "Select your state.",
        "Open the applicable official citizen-service portal.",
        "Select the relevant caste/community certificate service.",
        "Enter applicant and community details.",
        "Upload supporting documents.",
        "Submit the application.",
        "Save the acknowledgement/reference number.",
      ],
      fees:
        "Fees and service charges depend on the state and application channel.",
      processingTime:
        "Processing time varies according to verification requirements and the issuing authority.",
      mistakes: [
        "Providing incorrect personal information",
        "Uploading incomplete supporting evidence",
        "Selecting the wrong certificate category",
        "Not checking application status",
      ],
    },

    {
      id: "pan",
      name: "PAN Card",
      icon: "💳",
      description:
        "Permanent Account Number used for taxation and many financial and identification purposes in India.",
      keywords: [
        "pan",
        "pan card",
        "pancard",
        "permanent account number",
        "tax id",
        "tax number",
        "income tax",
      ],
      eligibility:
        "Individuals and eligible entities requiring PAN for taxation, financial transactions, employment, business or other legally permitted purposes.",
      documents: [
        "Proof of identity",
        "Proof of address",
        "Proof of date of birth, where applicable",
        "Photograph, where required",
        "Additional documents based on applicant type",
      ],
      steps: [
        "Use the authorised PAN application channel.",
        "Choose a new PAN or correction service.",
        "Enter the required applicant information.",
        "Submit identity and address details.",
        "Complete verification and applicable payment.",
        "Save the acknowledgement number.",
      ],
      fees:
        "Application charges depend on the application type and delivery method.",
      processingTime:
        "Processing time varies according to verification and application method.",
      mistakes: [
        "Incorrect name or date of birth",
        "Incorrect address",
        "Inconsistent supporting documents",
        "Applying for another PAN when one already exists",
      ],
    },

    {
      id: "birth",
      name: "Birth Certificate",
      icon: "👶",
      description:
        "Official record of birth used for proof of birth details and various legal and administrative purposes.",
      keywords: [
        "birth",
        "birth certificate",
        "baby",
        "newborn",
        "new born",
        "child birth",
        "born",
        "birth registration",
        "date of birth",
      ],
      eligibility:
        "Parents, guardians or eligible individuals can use the applicable birth-registration system for the place where the birth occurred.",
      documents: [
        "Hospital or birth record, where applicable",
        "Parent/guardian identity proof",
        "Address information",
        "Birth details",
        "Additional documents required by the local registration authority",
      ],
      steps: [
        "Identify the registration authority for the place of birth.",
        "Open the applicable official registration portal.",
        "Provide birth and parent details.",
        "Upload or submit supporting documents.",
        "Review the information.",
        "Submit the registration request.",
        "Save the registration/reference number.",
      ],
      fees:
        "Fees may depend on the registration timing, location and applicable rules.",
      processingTime:
        "Processing time varies by local registration authority.",
      mistakes: [
        "Incorrect date of birth",
        "Incorrect parent details",
        "Unclear supporting documents",
        "Applying through the wrong registration authority",
      ],
    },

    {
      id: "death",
      name: "Death Certificate",
      icon: "🕊️",
      description:
        "Official record of a person's death issued by the applicable local registration authority.",
      keywords: [
        "death",
        "death certificate",
        "death registration",
        "deceased",
        "dead",
        "death document",
      ],
      eligibility:
        "The death should be registered with the appropriate registration authority for the place where the death occurred.",
      documents: [
        "Medical/hospital death record, where applicable",
        "Identity details of the deceased",
        "Applicant identity proof",
        "Death details such as date and place",
        "Additional documents required by the local authority",
      ],
      steps: [
        "Identify the local birth/death registration authority.",
        "Open the applicable official portal.",
        "Provide details of the deceased.",
        "Upload or submit supporting records.",
        "Review the information.",
        "Submit the registration/application.",
        "Save the acknowledgement/reference number.",
      ],
      fees:
        "Fees may depend on location, registration timing and applicable local rules.",
      processingTime:
        "Processing time varies by local registration authority.",
      mistakes: [
        "Incorrect date of death",
        "Incorrect details of the deceased",
        "Using the wrong local registration authority",
        "Submitting incomplete supporting records",
      ],
    },

    {
      id: "aadhaar",
      name: "Aadhaar Services",
      icon: "🪪",
      description:
        "Official Aadhaar enrolment, update and related services provided through authorised UIDAI channels.",
      keywords: [
        "aadhaar",
        "aadhar",
        "uidai",
        "aadhaar card",
        "aadhaar update",
        "aadhaar correction",
        "aadhaar enrollment",
        "aadhaar enrolment",
      ],
      eligibility:
        "Residents seeking Aadhaar enrolment or eligible Aadhaar update services.",
      documents: [
        "Valid identity/address documents as applicable",
        "Supporting documents required for the requested update",
        "Existing Aadhaar details, where applicable",
      ],
      steps: [
        "Visit the official UIDAI website.",
        "Identify the required Aadhaar service.",
        "Follow the applicable online or enrolment-centre process.",
        "Provide the required documents.",
        "Complete verification/biometric requirements where applicable.",
        "Save the acknowledgement details.",
      ],
      fees:
        "UIDAI service charges vary depending on the type of service.",
      processingTime:
        "Processing time depends on the requested Aadhaar service.",
      mistakes: [
        "Using unofficial Aadhaar websites",
        "Providing incorrect information",
        "Not carrying required supporting documents",
      ],
    },

    /* ======================================================
       NEW SERVICES
    ====================================================== */

    {
      id: "passport",
      name: "Passport Services",
      icon: "🛂",
      description:
        "Official passport application, reissue and related services through the Passport Seva system.",
      keywords: [
        "passport",
        "passport application",
        "new passport",
        "passport reissue",
        "passport renewal",
        "passport seva",
        "tatkal passport",
      ],
      eligibility:
        "Eligible Indian citizens can use the official Passport Seva system for passport applications and related services according to applicable rules.",
      documents: [
        "Proof of identity",
        "Proof of address",
        "Proof of date of birth, where applicable",
        "Photograph or other documents as required by the application type",
      ],
      steps: [
        "Open the official Passport Seva portal.",
        "Register/login and choose the applicable passport service.",
        "Complete the application form.",
        "Upload/provide the required documents.",
        "Pay the applicable fee and schedule an appointment where required.",
        "Attend the designated Passport Seva Kendra or applicable centre.",
        "Track the application using the official Passport Seva system.",
      ],
      fees:
        "Passport fees depend on the application type and service category. Verify the current fee on the official portal.",
      processingTime:
        "Processing time varies according to application type, verification and other applicable requirements.",
      mistakes: [
        "Entering incorrect personal details",
        "Using incomplete or inconsistent documents",
        "Selecting the wrong application category",
        "Missing the scheduled appointment",
      ],
    },

    {
      id: "residence",
      name: "Residence / Domicile Certificate",
      icon: "🏠",
      description:
        "Certificate used to establish residence or domicile for eligible government, education and other official purposes.",
      keywords: [
        "residence",
        "residence certificate",
        "domicile",
        "domicile certificate",
        "resident certificate",
        "address certificate",
        "proof of residence",
        "permanent resident",
      ],
      eligibility:
        "Applicants who need official proof of residence or domicile and satisfy the applicable state or UT requirements.",
      documents: [
        "Identity proof",
        "Address proof",
        "Aadhaar or other accepted identification",
        "Utility bill or residence document, where applicable",
        "Self-declaration/affidavit, where required",
      ],
      steps: [
        "Select your state or UT.",
        "Open the official state citizen-service portal.",
        "Select Residence/Domicile Certificate.",
        "Enter the applicant and residence details.",
        "Upload the required documents.",
        "Submit the application and save the acknowledgement number.",
      ],
      fees:
        "Fees vary by state/UT and application channel.",
      processingTime:
        "Processing time varies by state and verification requirements.",
      mistakes: [
        "Using an outdated address",
        "Uploading insufficient residence proof",
        "Selecting the wrong service",
        "Not checking the application status",
      ],
    },

    {
      id: "marriage",
      name: "Marriage Certificate",
      icon: "💍",
      description:
        "Official registration and certificate of marriage through the competent registration authority.",
      keywords: [
        "marriage",
        "marriage certificate",
        "marriage registration",
        "register marriage",
        "wedding certificate",
        "married",
      ],
      eligibility:
        "Eligible couples can apply through the marriage registration authority applicable to their place of residence or marriage.",
      documents: [
        "Identity proof of both applicants",
        "Address proof",
        "Age/date-of-birth proof",
        "Marriage photographs",
        "Marriage invitation or other supporting proof, where applicable",
        "Witness documents, where required",
      ],
      steps: [
        "Select your state/UT.",
        "Open the applicable official registration portal.",
        "Select Marriage Registration.",
        "Enter details of both spouses.",
        "Upload required documents.",
        "Complete appointment/verification requirements where applicable.",
        "Submit and save the acknowledgement.",
      ],
      fees:
        "Registration fees vary by state, marriage type and applicable rules.",
      processingTime:
        "Processing time varies by registration authority.",
      mistakes: [
        "Incorrect names or dates",
        "Missing witness information",
        "Using incorrect address proof",
        "Missing appointment or verification requirements",
      ],
    },

    {
      id: "driving",
      name: "Driving Licence",
      icon: "🚗",
      description:
        "Application and related services for learner's and driving licences through the official transport system.",
      keywords: [
        "driving licence",
        "driving license",
        "dl",
        "learner licence",
        "learner license",
        "llr",
        "licence",
        "license",
        "rto",
      ],
      eligibility:
        "Applicants meeting the applicable age, documentation, medical and other transport requirements.",
      documents: [
        "Proof of identity",
        "Proof of address",
        "Age/date-of-birth proof",
        "Photograph where required",
        "Medical certificate where applicable",
      ],
      steps: [
        "Open the official Parivahan portal.",
        "Select your state/UT.",
        "Choose the appropriate licence service.",
        "Enter applicant details.",
        "Upload required documents.",
        "Pay the applicable fee.",
        "Complete the required test/appointment process.",
      ],
      fees:
        "Fees depend on the licence service and applicable transport rules.",
      processingTime:
        "Processing time depends on appointment, testing and RTO requirements.",
      mistakes: [
        "Selecting the wrong licence category",
        "Incorrect personal information",
        "Missing required documents",
        "Missing the driving test appointment",
      ],
    },

    {
      id: "voter",
      name: "Voter ID / Electoral Registration",
      icon: "🗳️",
      description:
        "Official electoral registration services including new voter registration and voter-detail updates.",
      keywords: [
        "voter",
        "voter id",
        "voter id card",
        "epic",
        "election card",
        "electoral roll",
        "new voter",
        "voting card",
      ],
      eligibility:
        "Eligible Indian citizens can use the official Election Commission voter services according to applicable electoral rules.",
      documents: [
        "Age proof",
        "Address proof",
        "Photograph",
        "Identity details",
        "Other documents required by the electoral authority",
      ],
      steps: [
        "Open the official Election Commission voter services portal.",
        "Select new registration or the required voter service.",
        "Enter personal and address information.",
        "Upload supporting documents.",
        "Submit the application.",
        "Track the application/reference number.",
      ],
      fees:
        "Official voter registration services are generally provided through the Election Commission's voter services system.",
      processingTime:
        "Processing time depends on electoral-roll verification.",
      mistakes: [
        "Incorrect address",
        "Incorrect age/date of birth",
        "Duplicate registration",
        "Uploading unclear documents",
      ],
    },

    {
      id: "ration",
      name: "Ration Card / Food Security",
      icon: "🍚",
      description:
        "Food-security and ration-card services administered through the relevant state/UT food and civil-supplies authority.",
      keywords: [
        "ration",
        "ration card",
        "food card",
        "food security",
        "nfsa",
        "pds",
        "public distribution",
        "food supply",
      ],
      eligibility:
        "Eligibility depends on the applicable state/UT food-security and public-distribution rules.",
      documents: [
        "Identity proof",
        "Address proof",
        "Family member details",
        "Income/category information where applicable",
        "Photographs where required",
      ],
      steps: [
        "Select your state/UT.",
        "Open the official food/civil-supplies portal.",
        "Choose the ration-card service.",
        "Enter household details.",
        "Upload supporting documents.",
        "Submit the application and save the reference number.",
      ],
      fees:
        "Fees depend on the state/UT and service requested.",
      processingTime:
        "Processing time varies according to local verification.",
      mistakes: [
        "Incorrect family details",
        "Duplicate family members",
        "Incorrect address",
        "Submitting incomplete documents",
      ],
    },

    {
      id: "ews",
      name: "EWS Certificate",
      icon: "📋",
      description:
        "Economically Weaker Section certificate for eligible applicants under applicable government rules.",
      keywords: [
        "ews",
        "ews certificate",
        "economically weaker section",
        "economic certificate",
        "ews reservation",
        "ews proof",
      ],
      eligibility:
        "Applicants meeting the applicable EWS income, asset and other eligibility requirements.",
      documents: [
        "Identity proof",
        "Address/residence proof",
        "Income-related documents",
        "Asset/property information where required",
        "Self-declaration/affidavit where applicable",
      ],
      steps: [
        "Select your state/UT.",
        "Open the official citizen-service portal.",
        "Select EWS/Income and Asset Certificate where available.",
        "Enter applicant and family information.",
        "Upload supporting documents.",
        "Submit the application and retain the acknowledgement.",
      ],
      fees:
        "Fees vary by state/UT and application method.",
      processingTime:
        "Processing time varies according to verification.",
      mistakes: [
        "Incorrect income information",
        "Missing asset information",
        "Using outdated documents",
        "Selecting an incorrect certificate service",
      ],
    },

    {
      id: "scholarship",
      name: "Government Scholarships",
      icon: "🎓",
      description:
        "Government scholarship discovery and application services for eligible students.",
      keywords: [
        "scholarship",
        "student scholarship",
        "education scholarship",
        "college scholarship",
        "school scholarship",
        "post matric scholarship",
        "pre matric scholarship",
        "scholarships",
      ],
      eligibility:
        "Eligibility depends on the particular scholarship, course, institution, category, income and other applicable conditions.",
      documents: [
        "Student identity proof",
        "Academic records",
        "Income certificate where required",
        "Caste/community certificate where applicable",
        "Bank account details",
        "Institution details",
      ],
      steps: [
        "Open the official National Scholarship Portal or applicable state scholarship portal.",
        "Register/login.",
        "Find the applicable scholarship.",
        "Complete the application.",
        "Upload the required documents.",
        "Submit and track verification/status.",
      ],
      fees:
        "Government scholarship applications generally do not require payment to private agents. Verify the official portal before submitting.",
      processingTime:
        "Processing depends on institution and government verification.",
      mistakes: [
        "Incorrect bank details",
        "Uploading invalid certificates",
        "Missing institution verification",
        "Applying for an incorrect scholarship",
      ],
    },

    {
      id: "vehicle",
      name: "Vehicle Registration / RC",
      icon: "🚘",
      description:
        "Vehicle registration and Registration Certificate services through the official transport system.",
      keywords: [
        "vehicle registration",
        "rc",
        "registration certificate",
        "car registration",
        "bike registration",
        "vehicle rc",
        "vehicle",
        "motor vehicle",
      ],
      eligibility:
        "Vehicle owners requiring registration or eligible registration-related services.",
      documents: [
        "Vehicle sale/invoice documents",
        "Identity proof",
        "Address proof",
        "Insurance documents",
        "Form and vehicle documents as applicable",
      ],
      steps: [
        "Open the official Parivahan portal.",
        "Select your state/UT.",
        "Choose the vehicle registration service.",
        "Enter vehicle and owner details.",
        "Upload/submit required documents.",
        "Complete applicable inspection and payment requirements.",
      ],
      fees:
        "Fees depend on vehicle type, state and registration service.",
      processingTime:
        "Processing time depends on RTO verification and vehicle inspection.",
      mistakes: [
        "Incorrect vehicle information",
        "Missing insurance",
        "Incorrect owner information",
        "Missing RTO inspection",
      ],
    },

    {
      id: "trade",
      name: "Trade / Business Licence",
      icon: "🏢",
      description:
        "Local business and trade-licence services administered by the applicable state or local authority.",
      keywords: [
        "trade license",
        "trade licence",
        "business licence",
        "business license",
        "shop license",
        "shop licence",
        "business registration",
        "trade registration",
      ],
      eligibility:
        "Businesses requiring a local trade or business licence according to applicable municipal/state rules.",
      documents: [
        "Identity proof",
        "Business address proof",
        "Property/occupancy documents where applicable",
        "Business details",
        "Other documents required by the local authority",
      ],
      steps: [
        "Select your state/UT.",
        "Identify the applicable municipal or state portal.",
        "Select Trade/Business Licence.",
        "Enter business details.",
        "Upload supporting documents.",
        "Pay the applicable fee and submit.",
      ],
      fees:
        "Fees vary by local authority, business type and location.",
      processingTime:
        "Processing time varies by local authority.",
      mistakes: [
        "Incorrect business address",
        "Missing occupancy documents",
        "Selecting the wrong licence category",
        "Not renewing on time",
      ],
    },

    {
      id: "farmer",
      name: "PM-KISAN / Farmer Services",
      icon: "🌾",
      description:
        "Government agricultural and farmer-support services including PM-KISAN-related services.",
      keywords: [
        "farmer",
        "farmer scheme",
        "pm kisan",
        "pm-kisan",
        "agriculture",
        "kisan",
        "farmer payment",
        "farmer registration",
        "agriculture scheme",
      ],
      eligibility:
        "Eligibility depends on the specific farmer scheme and applicable government rules.",
      documents: [
        "Aadhaar/identity details",
        "Land or farmer records where applicable",
        "Bank account details",
        "Mobile number",
        "Other documents required under the scheme",
      ],
      steps: [
        "Open the official PM-KISAN or applicable agriculture portal.",
        "Select the required farmer service.",
        "Enter applicant details.",
        "Complete required verification.",
        "Submit the application.",
        "Track the application/payment status.",
      ],
      fees:
        "Verify the official scheme portal. Do not pay unofficial agents for government scheme registration.",
      processingTime:
        "Processing depends on verification and applicable scheme procedures.",
      mistakes: [
        "Incorrect Aadhaar details",
        "Incorrect bank account information",
        "Incorrect land information",
        "Not completing required verification",
      ],
    },

    {
      id: "disability",
      name: "Disability Certificate / UDID",
      icon: "♿",
      description:
        "Disability certification and UDID-related services through the official government system.",
      keywords: [
        "disability",
        "disability certificate",
        "udid",
        "unique disability id",
        "pwd certificate",
        "divyang certificate",
        "disabled certificate",
      ],
      eligibility:
        "Eligible persons with disabilities can apply according to the applicable assessment and certification requirements.",
      documents: [
        "Identity proof",
        "Address details",
        "Medical records where applicable",
        "Existing disability records where available",
        "Photograph",
      ],
      steps: [
        "Open the official UDID portal.",
        "Register/login.",
        "Complete the disability certificate/UDID application.",
        "Upload the required documents.",
        "Attend the required medical assessment.",
        "Track the application status.",
      ],
      fees:
        "Verify the official UDID portal for current requirements.",
      processingTime:
        "Processing depends on medical assessment and certification.",
      mistakes: [
        "Missing medical records",
        "Incorrect personal information",
        "Missing assessment appointment",
      ],
    },

    {
      id: "senior",
      name: "Senior Citizen Certificate",
      icon: "👴",
      description:
        "Certificate or related services for senior citizens where provided by the applicable state/UT authority.",
      keywords: [
        "senior citizen",
        "senior citizen certificate",
        "old age certificate",
        "elderly certificate",
        "senior card",
      ],
      eligibility:
        "Eligibility depends on the applicable age and state/UT rules.",
      documents: [
        "Identity proof",
        "Age/date-of-birth proof",
        "Address proof",
        "Photograph where required",
      ],
      steps: [
        "Select your state/UT.",
        "Open the applicable official citizen-service portal.",
        "Select the senior citizen service if available.",
        "Enter applicant details.",
        "Upload documents.",
        "Submit and save the acknowledgement.",
      ],
      fees:
        "Fees depend on the state/UT and service.",
      processingTime:
        "Processing time varies by authority.",
      mistakes: [
        "Incorrect date of birth",
        "Incorrect address",
        "Missing age proof",
      ],
    },

    {
      id: "ayushman",
      name: "Ayushman Bharat / Health Services",
      icon: "🏥",
      description:
        "Official government health-benefit and beneficiary services under applicable national health programmes.",
      keywords: [
        "ayushman",
        "ayushman bharat",
        "health card",
        "pmjay",
        "pm jay",
        "health scheme",
        "government health",
        "hospital scheme",
      ],
      eligibility:
        "Eligibility depends on the applicable government health programme and beneficiary criteria.",
      documents: [
        "Aadhaar or accepted identity document",
        "Mobile number",
        "Beneficiary/family details",
        "Other documents as required",
      ],
      steps: [
        "Open the official National Health Authority beneficiary portal.",
        "Check beneficiary eligibility.",
        "Complete the required verification.",
        "Follow the instructions for obtaining/using the health benefit.",
      ],
      fees:
        "Verify eligibility and service details only through official government channels.",
      processingTime:
        "Depends on beneficiary verification and service requirements.",
      mistakes: [
        "Using unofficial websites",
        "Incorrect beneficiary information",
        "Sharing OTP or sensitive information with agents",
      ],
    },

    {
      id: "employment",
      name: "Employment / Job-Seeker Registration",
      icon: "💼",
      description:
        "Government employment and job-seeker registration services through the National Career Service.",
      keywords: [
        "job",
        "jobs",
        "job seeker",
        "jobseeker",
        "employment",
        "employment registration",
        "government jobs",
        "career",
        "job registration",
      ],
      eligibility:
        "Job seekers can register on the government employment platform and use applicable services.",
      documents: [
        "Identity details",
        "Educational qualification information",
        "Contact information",
        "Employment/experience details where applicable",
        "Resume where applicable",
      ],
      steps: [
        "Open the official National Career Service portal.",
        "Register as a job seeker.",
        "Complete your profile.",
        "Add education and skills.",
        "Search applicable opportunities.",
        "Apply through the official platform where available.",
      ],
      fees:
        "Verify the official National Career Service portal. Be cautious of anyone asking for payment for government job registration.",
      processingTime:
        "Registration is subject to successful account/profile verification.",
      mistakes: [
        "Incorrect education details",
        "Incomplete profile",
        "Sharing account credentials",
        "Paying unofficial agents",
      ],
    },
    {
      id: "pension",
      name: "Pension / Social Security Services",
      icon: "👵",
      description:
        "Government pension and social-security services for eligible beneficiaries through applicable official portals.",
      keywords: [
        "pension",
        "pension scheme",
        "old age pension",
        "senior pension",
        "widow pension",
        "social security",
        "pension application",
      ],
      eligibility:
        "Eligibility depends on the specific pension or social-security scheme and applicable central or state/UT rules.",
      documents: [
        "Identity proof",
        "Address/residence proof",
        "Age proof where applicable",
        "Bank account details",
        "Income/category or other scheme-specific documents where required",
      ],
      steps: [
        "Select your state/UT if a state-administered pension service applies.",
        "Open the applicable official government pension/social-security portal.",
        "Check eligibility for the relevant scheme.",
        "Complete the application with the required details.",
        "Upload/submit supporting documents.",
        "Submit and save the acknowledgement/reference number.",
        "Track the application through the official system.",
      ],
      fees:
        "Verify the official scheme portal. Do not pay unofficial agents for government pension registration.",
      processingTime:
        "Processing time varies according to the scheme, verification and issuing authority.",
      mistakes: [
        "Incorrect bank account details",
        "Incorrect age or personal information",
        "Missing scheme-specific documents",
        "Paying unofficial agents for registration",
      ],
    },

  ];

  /* ========================================================
     UNIFIED SERVICE DATA

     All existing frontend services are preserved.
     SQL data enriches matching services.
     Frontend-only services do NOT disappear.
     Existing IDs, icons, keywords and mistakes are preserved.
     Existing official URL maps are not overwritten.
  ======================================================== */
        /* ========================================================
     LOAD COMPLETE SERVICE FROM DATABASE
  ======================================================== */

  const loadServiceDetails = async (serviceId) => {
    try {
      const service = await getService(serviceId);

      const toArray = (value) => {
        if (Array.isArray(value)) {
          return value;
        }

        if (!value) {
          return [];
        }

        if (typeof value === "string") {
          try {
            const parsed = JSON.parse(value);

            if (Array.isArray(parsed)) {
              return parsed;
            }
          } catch {
            // Value is not JSON
          }

          return value
            .split(/\r?\n|\s*;\s*/)
            .map((item) => item.trim())
            .filter(Boolean);
        }

        return [];
      };

      return {
        ...service,

        documents: toArray(service.documents),

        steps: toArray(service.steps),

        processingTime:
          service.processing_time ||
          "Processing time varies by service.",

        officialPortalName:
          service.official_portal_name || "",

        officialPortalUrl:
          service.official_portal_url || "",
      };

    } catch (error) {
      console.error(
        "Failed to load service details from database:",
        error
      );

      return null;
    }
  };
    const unifiedServices = [
    ...services.map((service) => {
      const dbService = dbServices.find(
        (item) =>
          item.name?.trim().toLowerCase() ===
          service.name?.trim().toLowerCase()
      );

      if (!dbService) {
        return service;
      }

      return {
        ...service,
        description: dbService.description || service.description,
        eligibility: dbService.eligibility || service.eligibility,
        documents:
          Array.isArray(dbService.documents) &&
          dbService.documents.length > 0
            ? dbService.documents
            : service.documents,
        steps:
          Array.isArray(dbService.steps) && dbService.steps.length > 0
            ? dbService.steps
            : service.steps,
        fees: dbService.fees || service.fees,
        processingTime:
          dbService.processingTime ||
          dbService.processing_time ||
          service.processingTime,
      };
    }),

    ...dbServices
      .filter(
        (dbService) =>
          !services.some(
            (service) =>
              service.name?.trim().toLowerCase() ===
              dbService.name?.trim().toLowerCase()
          )
      )
      .map((dbService) => ({
        id: String(dbService.id ?? dbService.name)
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, "-")
          .replace(/^-|-$/g, ""),
        name: dbService.name,
        icon: "🏛️",
        description: dbService.description || "Government service",
        keywords: [
          dbService.name,
          ...(dbService.category ? [dbService.category] : []),
        ],
        eligibility:
          dbService.eligibility ||
          "Check the official government portal for eligibility requirements.",
        documents: Array.isArray(dbService.documents)
          ? dbService.documents
          : [],
        steps: Array.isArray(dbService.steps) ? dbService.steps : [],
        fees:
          dbService.fees ||
          "Check the official government portal for current fees.",
        processingTime:
          dbService.processingTime ||
          dbService.processing_time ||
          "Processing time varies by service and authority.",
        mistakes: [],
      })),
  ];

  /* ========================================================
     EXISTING VERIFIED STATE + SERVICE LINKS
     DO NOT CHANGE THESE EXISTING LINKS
  ======================================================== */

  const stateServiceLinks = {
    "Andhra Pradesh": {
      income: {
        name: "AP MeeSeva",
        url: "https://ap.meeseva.gov.in/",
      },
      caste: {
        name: "AP MeeSeva",
        url: "https://ap.meeseva.gov.in/",
      },
      birth: {
        name: "AP MeeSeva",
        url: "https://ap.meeseva.gov.in/",
      },
      death: {
        name: "AP MeeSeva",
        url: "https://ap.meeseva.gov.in/",
      },
      aadhaar: {
        name: "UIDAI Aadhaar Services",
        url: "https://uidai.gov.in/",
      },
    },

    Telangana: {
      income: {
        name: "Telangana MeeSeva",
        url: "https://ts.meeseva.telangana.gov.in/",
      },
      "caste": {
    name: "Telangana MeeSeva - Caste Certificate",
    url: "https://ts.meeseva.telangana.gov.in/TSDeptPortal/UserInterface/serviceapplication.aspx"
},
      birth: {
        name: "Telangana MeeSeva",
        url: "https://ts.meeseva.telangana.gov.in/",
      },
      death: {
        name: "Telangana MeeSeva",
        url: "https://ts.meeseva.telangana.gov.in/",
      },
      aadhaar: {
        name: "UIDAI Aadhaar Services",
        url: "https://uidai.gov.in/",
      },
    },

    Karnataka: {
      income: {
        name: "Karnataka Seva Sindhu",
        url: "https://sevasindhu.karnataka.gov.in/",
      },
      caste: {
        name: "Karnataka Seva Sindhu",
        url: "https://sevasindhu.karnataka.gov.in/",
      },
      birth: {
        name: "Karnataka Birth Certificate Service",
        url: "https://services.india.gov.in/service/detail/apply-for-birth-certificate-karnataka",
      },
      death: {
        name: "Karnataka Death Certificate Service",
        url: "https://services.india.gov.in/service/detail/apply-for-death-certificate-karnataka",
      },
      aadhaar: {
        name: "UIDAI Aadhaar Services",
        url: "https://uidai.gov.in/",
      },
    },

    "Tamil Nadu": {
      income: {
        name: "Tamil Nadu e-Sevai",
        url: "https://www.tnesevai.tn.gov.in/",
      },
      caste: {
        name: "Tamil Nadu e-Sevai",
        url: "https://www.tnesevai.tn.gov.in/",
      },
      birth: {
        name: "Tamil Nadu e-Sevai",
        url: "https://www.tnesevai.tn.gov.in/",
      },
      death: {
        name: "Tamil Nadu e-Sevai",
        url: "https://www.tnesevai.tn.gov.in/",
      },
        residence: {
    name: "Telangana MeeSeva - Residence Certificate",
    url: "https://ts.meeseva.telangana.gov.in/meeseva/login.htm",
  },
      aadhaar: {
        name: "UIDAI Aadhaar Services",
        url: "https://uidai.gov.in/",
      },
    },

    Kerala: {
      income: {
        name: "Kerala e-District",
        url: "https://edistrict.kerala.gov.in/",
      },
      caste: {
        name: "Kerala e-District",
        url: "https://edistrict.kerala.gov.in/",
      },
      birth: {
        name: "Kerala K-SMART / Local Self Government",
        url: "https://lsgkerala.gov.in/",
      },
      death: {
        name: "Kerala K-SMART / Local Self Government",
        url: "https://lsgkerala.gov.in/",
      },
      aadhaar: {
        name: "UIDAI Aadhaar Services",
        url: "https://uidai.gov.in/",
      },
    },

    Gujarat: {
      income: {
        name: "Digital Gujarat",
        url: "https://www.digitalgujarat.gov.in/",
      },
      caste: {
        name: "Digital Gujarat",
        url: "https://www.digitalgujarat.gov.in/",
      },
      birth: {
        name: "Digital Gujarat",
        url: "https://www.digitalgujarat.gov.in/",
      },
      death: {
        name: "Digital Gujarat",
        url: "https://www.digitalgujarat.gov.in/",
      },
      aadhaar: {
        name: "UIDAI Aadhaar Services",
        url: "https://uidai.gov.in/",
      },
    },

    Maharashtra: {
      income: {
        name: "Aaple Sarkar",
        url: "https://aaplesarkar.mahaonline.gov.in/",
      },
      caste: {
        name: "Aaple Sarkar",
        url: "https://aaplesarkar.mahaonline.gov.in/",
      },
      birth: {
        name: "Aaple Sarkar",
        url: "https://aaplesarkar.mahaonline.gov.in/",
      },
      death: {
        name: "Aaple Sarkar",
        url: "https://aaplesarkar.mahaonline.gov.in/",
      },
      aadhaar: {
        name: "UIDAI Aadhaar Services",
        url: "https://uidai.gov.in/",
      },
    },

    "Madhya Pradesh": {
      income: {
        name: "MP e-District",
        url: "https://mpedistrict.gov.in/",
      },
      caste: {
        name: "MP e-District",
        url: "https://mpedistrict.gov.in/",
      },
      birth: {
        name: "MP e-District",
        url: "https://mpedistrict.gov.in/",
      },
      death: {
        name: "MP e-District",
        url: "https://mpedistrict.gov.in/",
      },
      aadhaar: {
        name: "UIDAI Aadhaar Services",
        url: "https://uidai.gov.in/",
      },
    },

    Rajasthan: {
      income: {
        name: "Rajasthan SSO",
        url: "https://sso.rajasthan.gov.in/",
      },
      caste: {
        name: "Rajasthan SSO",
        url: "https://sso.rajasthan.gov.in/",
      },
      birth: {
        name: "Rajasthan SSO",
        url: "https://sso.rajasthan.gov.in/",
      },
      death: {
        name: "Rajasthan SSO",
        url: "https://sso.rajasthan.gov.in/",
      },
      aadhaar: {
        name: "UIDAI Aadhaar Services",
        url: "https://uidai.gov.in/",
      },
    },

    Odisha: {
      income: {
        name: "Odisha One",
        url: "https://odishaone.gov.in/",
      },
      caste: {
        name: "Odisha One",
        url: "https://odishaone.gov.in/",
      },
      birth: {
        name: "Odisha One",
        url: "https://odishaone.gov.in/",
      },
      death: {
        name: "Odisha One",
        url: "https://odishaone.gov.in/",
      },
      aadhaar: {
        name: "UIDAI Aadhaar Services",
        url: "https://uidai.gov.in/",
      },
    },

    Haryana: {
      income: {
        name: "Haryana SARAL",
        url: "https://saralharyana.gov.in/",
      },
      caste: {
        name: "Haryana SARAL",
        url: "https://saralharyana.gov.in/",
      },
      birth: {
        name: "Haryana SARAL",
        url: "https://saralharyana.gov.in/",
      },
      death: {
        name: "Haryana SARAL",
        url: "https://saralharyana.gov.in/",
      },
      aadhaar: {
        name: "UIDAI Aadhaar Services",
        url: "https://uidai.gov.in/",
      },
    },

    Punjab: {
      income: {
        name: "Punjab Connect",
        url: "https://connect.punjab.gov.in/",
      },
      caste: {
        name: "Punjab Connect",
        url: "https://connect.punjab.gov.in/",
      },
      birth: {
        name: "Punjab Connect",
        url: "https://connect.punjab.gov.in/",
      },
      death: {
        name: "Punjab Connect",
        url: "https://connect.punjab.gov.in/",
      },
      aadhaar: {
        name: "UIDAI Aadhaar Services",
        url: "https://uidai.gov.in/",
      },
    },

    "Uttar Pradesh": {
      income: {
        name: "UP e-District",
        url: "https://edistrict.up.gov.in/",
      },
      caste: {
        name: "UP e-District",
        url: "https://edistrict.up.gov.in/",
      },
      birth: {
        name: "UP e-District",
        url: "https://edistrict.up.gov.in/",
      },
      death: {
        name: "UP e-District",
        url: "https://edistrict.up.gov.in/",
      },
      aadhaar: {
        name: "UIDAI Aadhaar Services",
        url: "https://uidai.gov.in/",
      },
    },

    Uttarakhand: {
      income: {
        name: "Uttarakhand e-District",
        url: "https://edistrict.uk.gov.in/",
      },
      caste: {
        name: "Uttarakhand e-District",
        url: "https://edistrict.uk.gov.in/",
      },
      birth: {
        name: "Uttarakhand e-District",
        url: "https://edistrict.uk.gov.in/",
      },
      death: {
        name: "Uttarakhand e-District",
        url: "https://edistrict.uk.gov.in/",
      },
      aadhaar: {
        name: "UIDAI Aadhaar Services",
        url: "https://uidai.gov.in/",
      },
    },

    Bihar: {
      income: {
        name: "Bihar RTPS",
        url: "https://serviceonline.bihar.gov.in/",
      },
      caste: {
        name: "Bihar RTPS",
        url: "https://serviceonline.bihar.gov.in/",
      },
      birth: {
        name: "Bihar RTPS",
        url: "https://serviceonline.bihar.gov.in/",
      },
      death: {
        name: "Bihar RTPS",
        url: "https://serviceonline.bihar.gov.in/",
      },
      aadhaar: {
        name: "UIDAI Aadhaar Services",
        url: "https://uidai.gov.in/",
      },
    },

    Jharkhand: {
      income: {
        name: "JharSewa",
        url: "https://jharsewa.jharkhand.gov.in/",
      },
      caste: {
        name: "JharSewa",
        url: "https://jharsewa.jharkhand.gov.in/",
      },
      birth: {
        name: "JharSewa",
        url: "https://jharsewa.jharkhand.gov.in/",
      },
      death: {
        name: "JharSewa",
        url: "https://jharsewa.jharkhand.gov.in/",
      },
      aadhaar: {
        name: "UIDAI Aadhaar Services",
        url: "https://uidai.gov.in/",
      },
    },

    Chhattisgarh: {
      income: {
        name: "CG e-District",
        url: "https://edistrict.cgstate.gov.in/",
      },
      caste: {
        name: "CG e-District",
        url: "https://edistrict.cgstate.gov.in/",
      },
      birth: {
        name: "CG e-District",
        url: "https://edistrict.cgstate.gov.in/",
      },
      death: {
        name: "CG e-District",
        url: "https://edistrict.cgstate.gov.in/",
      },
      aadhaar: {
        name: "UIDAI Aadhaar Services",
        url: "https://uidai.gov.in/",
      },
    },

    Goa: {
      income: {
        name: "Goa Online",
        url: "https://goaonline.gov.in/",
      },
      caste: {
        name: "Goa Online",
        url: "https://goaonline.gov.in/",
      },
      birth: {
        name: "Goa Online",
        url: "https://goaonline.gov.in/",
      },
      death: {
        name: "Goa Online",
        url: "https://goaonline.gov.in/",
      },
      aadhaar: {
        name: "UIDAI Aadhaar Services",
        url: "https://uidai.gov.in/",
      },
    },

    "West Bengal": {
      income: {
        name: "West Bengal e-District",
        url: "https://edistrict.wb.gov.in/",
      },
      caste: {
        name: "West Bengal e-District",
        url: "https://edistrict.wb.gov.in/",
      },
      birth: {
        name: "West Bengal e-District",
        url: "https://edistrict.wb.gov.in/",
      },
      death: {
        name: "West Bengal e-District",
        url: "https://edistrict.wb.gov.in/",
      },
      aadhaar: {
        name: "UIDAI Aadhaar Services",
        url: "https://uidai.gov.in/",
      },
    },

    "Himachal Pradesh": {
      income: {
        name: "Himachal e-District",
        url: "https://edistrict.hp.gov.in/",
      },
      caste: {
        name: "Himachal e-District",
        url: "https://edistrict.hp.gov.in/",
      },
      birth: {
        name: "Himachal e-District",
        url: "https://edistrict.hp.gov.in/",
      },
      death: {
        name: "Himachal e-District",
        url: "https://edistrict.hp.gov.in/",
      },
      aadhaar: {
        name: "UIDAI Aadhaar Services",
        url: "https://uidai.gov.in/",
      },
    },

    "Jammu and Kashmir": {
      income: {
        name: "J&K e-Services",
        url: "https://serviceonline.jammu.gov.in/",
      },
      caste: {
        name: "J&K e-Services",
        url: "https://serviceonline.jammu.gov.in/",
      },
      birth: {
        name: "J&K e-Services",
        url: "https://serviceonline.jammu.gov.in/",
      },
      death: {
        name: "J&K e-Services",
        url: "https://serviceonline.jammu.gov.in/",
      },
      aadhaar: {
        name: "UIDAI Aadhaar Services",
        url: "https://uidai.gov.in/",
      },
    },

    Delhi: {
      income: {
        name: "Delhi e-District",
        url: "https://edistrict.delhigovt.nic.in/",
      },
      caste: {
        name: "Delhi e-District",
        url: "https://edistrict.delhigovt.nic.in/",
      },
      birth: {
        name: "Delhi e-District",
        url: "https://edistrict.delhigovt.nic.in/",
      },
      death: {
        name: "Delhi e-District",
        url: "https://edistrict.delhigovt.nic.in/",
      },
      aadhaar: {
        name: "UIDAI Aadhaar Services",
        url: "https://uidai.gov.in/",
      },
    },

    "Arunachal Pradesh": {
      aadhaar: {
        name: "UIDAI Aadhaar Services",
        url: "https://uidai.gov.in/",
      },
    },

    Assam: {
      aadhaar: {
        name: "UIDAI Aadhaar Services",
        url: "https://uidai.gov.in/",
      },
    },

    Manipur: {
      aadhaar: {
        name: "UIDAI Aadhaar Services",
        url: "https://uidai.gov.in/",
      },
    },

    Meghalaya: {
      aadhaar: {
        name: "UIDAI Aadhaar Services",
        url: "https://uidai.gov.in/",
      },
    },

    Mizoram: {
      aadhaar: {
        name: "UIDAI Aadhaar Services",
        url: "https://uidai.gov.in/",
      },
    },

    Nagaland: {
      aadhaar: {
        name: "UIDAI Aadhaar Services",
        url: "https://uidai.gov.in/",
      },
    },

    Sikkim: {
      aadhaar: {
        name: "UIDAI Aadhaar Services",
        url: "https://uidai.gov.in/",
      },
    },

    Tripura: {
      aadhaar: {
        name: "UIDAI Aadhaar Services",
        url: "https://uidai.gov.in/",
      },
    },

    "Andaman and Nicobar Islands": {
      aadhaar: {
        name: "UIDAI Aadhaar Services",
        url: "https://uidai.gov.in/",
      },
    },

    Chandigarh: {
      aadhaar: {
        name: "UIDAI Aadhaar Services",
        url: "https://uidai.gov.in/",
      },
    },

    "Dadra and Nagar Haveli and Daman and Diu": {
      aadhaar: {
        name: "UIDAI Aadhaar Services",
        url: "https://uidai.gov.in/",
      },
    },

    Ladakh: {
      aadhaar: {
        name: "UIDAI Aadhaar Services",
        url: "https://uidai.gov.in/",
      },
    },

    Lakshadweep: {
      aadhaar: {
        name: "UIDAI Aadhaar Services",
        url: "https://uidai.gov.in/",
      },
    },

    Puducherry: {
      aadhaar: {
        name: "UIDAI Aadhaar Services",
        url: "https://uidai.gov.in/",
      },
    },
  };

  /* ========================================================
     NEW SERVICE LINKS
     Existing links above are NOT modified.
  ======================================================== */

  const nationalServiceLinks = {
    passport: {
      name: "Passport Seva",
      url: "https://www.passportindia.gov.in/",
    },

    pan: {
      name: "Income Tax e-Filing / PAN Services",
      url: "https://www.incometax.gov.in/",
    },

    aadhaar: {
      name: "UIDAI Aadhaar Services",
      url: "https://uidai.gov.in/",
    },

    driving: {
      name: "Parivahan Sewa",
      url: "https://parivahan.gov.in/",
    },

    voter: {
      name: "Election Commission Voter Services",
      url: "https://voters.eci.gov.in/",
    },

    scholarship: {
      name: "National Scholarship Portal",
      url: "https://scholarships.gov.in/",
    },

    vehicle: {
      name: "Parivahan Sewa",
      url: "https://parivahan.gov.in/",
    },

    farmer: {
      name: "PM-KISAN",
      url: "https://pmkisan.gov.in/",
    },

    disability: {
      name: "UDID - Unique Disability ID",
      url: "https://www.swavlambancard.gov.in/",
    },

    ayushman: {
      name: "Ayushman Bharat / National Health Authority",
      url: "https://beneficiary.nha.gov.in/",
    },

    employment: {
      name: "National Career Service",
      url: "https://www.ncs.gov.in/",
    },

    ration: {
      name: "National Food Security Portal",
      url: "https://nfsa.gov.in/",
    },

    pension: {
      name: "National Social Assistance Programme",
      url: "https://nsap.nic.in/",
    },
  };

  /* ========================================================
     STATE PORTAL FALLBACKS FOR STATE-ADMINISTERED SERVICES
     Existing service-specific links always take priority.
  ======================================================== */

  const statePortalFallbacks = {
    "Andhra Pradesh": "https://vswsonline.ap.gov.in/",
    "Arunachal Pradesh": "https://eservice.arunachal.gov.in/",
    "Assam": "https://sewasetu.assam.gov.in/",
    "Bihar": "https://serviceonline.bihar.gov.in/",
    "Chhattisgarh": "https://edistrict.cgstate.gov.in/",
    "Goa": "https://goaonline.gov.in/",
    "Gujarat": "https://digitalgujarat.gov.in/",
    "Haryana": "https://saralharyana.gov.in/",
    "Himachal Pradesh": "https://himseva.hp.gov.in/",
    "Jharkhand": "https://jharsewa.jharkhand.gov.in/",
    "Karnataka": "https://sevasindhu.karnataka.gov.in/",
    "Kerala": "https://services.kerala.gov.in/",
    "Madhya Pradesh": "https://services.mp.gov.in/",
    "Maharashtra": "https://aaplesarkar.mahaonline.gov.in/",
    "Manipur": "https://uspmanipur.mn.gov.in/",
    "Meghalaya": "https://meghalayaone.gov.in/",
    "Mizoram": "https://services.india.gov.in/service/listing",
    "Nagaland": "https://edistrict.nagaland.gov.in/",
    "Odisha": "https://odishaone.gov.in/",
    "Punjab": "https://connect.punjab.gov.in/",
    "Rajasthan": "https://emitra.rajasthan.gov.in/",
    "Sikkim": "https://sso.sikkim.gov.in/",
    "Tamil Nadu": "https://tnesevai.tn.gov.in/",
    "Telangana": "https://ts.meeseva.telangana.gov.in/",
    "Tripura": "https://edistrict.tripura.gov.in/",
    "Uttar Pradesh": "https://edistrict.up.gov.in/",
    "Uttarakhand": "https://eservices.uk.gov.in/",
    "West Bengal": "https://edistrict.wb.gov.in/",
    "Andaman and Nicobar Islands": "https://anieseva.andaman.gov.in/",
    "Chandigarh": "https://eservices.chd.gov.in/",
    "Dadra and Nagar Haveli and Daman and Diu": "https://swp.dddgov.in/",
    "Delhi": "https://edistrict.delhi.gov.in/",
    "Jammu and Kashmir": "https://eunnat.jk.gov.in/",
    "Ladakh": "https://eseva.ladakh.gov.in/",
    "Lakshadweep": "https://services.india.gov.in/service/listing",
    "Puducherry": "https://edistrict.py.gov.in/",
  };

  /* ========================================================
     GET SERVICE LINK
  ======================================================== */

  const getServiceLink = (service) => {
    if (!selectedState || !service) {
      return null;
    }

    /*
      PRIMARY SOURCE:
      Use the state-specific service record loaded from FastAPI/SQLite.

      The seed database contains one record for every:
        22 services × 36 states/UTs = 792 combinations.

      IMPORTANT:
      We match BOTH service name and state_id. Matching by service name
      alone can accidentally select the wrong state's portal.
    */
    const selectedStateRecord = dbStates.find(
      (state) =>
        state?.name?.trim().toLowerCase() ===
        selectedState.trim().toLowerCase()
    );

    const selectedStateId = Number(selectedStateRecord?.id);

    const serviceName = service?.name?.trim().toLowerCase();

    const databaseService = dbServices.find((item) => {
      const itemName = item?.name?.trim().toLowerCase();
      const itemStateId = Number(item?.state_id);

      return (
        itemName === serviceName &&
        Number.isInteger(selectedStateId) &&
        itemStateId === selectedStateId
      );
    });

    if (databaseService?.official_portal_url) {
      return {
        name:
          databaseService.official_portal_name ||
          `${selectedState} Official Government Service Portal`,
        url: databaseService.official_portal_url,
      };
    }

    /*
      SECONDARY SOURCE:
      The selected service itself may already contain an official URL.
    */
    if (service?.officialPortalUrl) {
      return {
        name:
          service.officialPortalName ||
          "Official Government Service Portal",
        url: service.officialPortalUrl,
      };
    }

    if (service?.official_portal_url) {
      return {
        name:
          service.official_portal_name ||
          "Official Government Service Portal",
        url: service.official_portal_url,
      };
    }

    /*
      THIRD SOURCE:
      Preserve the existing verified service-specific links.
    */
    const stateLinks = stateServiceLinks[selectedState];

    if (stateLinks && stateLinks[service.id]) {
      return stateLinks[service.id];
    }

    /*
      FOURTH SOURCE:
      National services such as Aadhaar, PAN, Passport, Voter ID,
      Parivahan, scholarships, PM-KISAN, UDID, Ayushman and NCS.
    */
    if (nationalServiceLinks[service.id]) {
      return nationalServiceLinks[service.id];
    }

    /*
      FINAL STATE/UT FALLBACK:
      Every state/UT in the application has an official portal.
      This prevents any service card from ending with "no portal".
    */
    if (statePortalFallbacks[selectedState]) {
      return {
        name: `${selectedState} Official Citizen Services`,
        url: statePortalFallbacks[selectedState],
      };
    }

    /*
      Last-resort official government directory.
    */
    return {
      name: "National Government Services Portal",
      url: "https://services.india.gov.in/service/listing",
    };
  };

  {/* ============================================================
    SEARCH ANALYTICS DASHBOARD
    ============================================================ */}

 
  /* ========================================================
     NORMALIZE
  ======================================================== */

  const normalizeText = (text) =>
    text
      .toLowerCase()
      .replace(/[^\w\s]/gi, " ")
      .replace(/\s+/g, " ")
      .trim();

  /* ========================================================
     MATCHING
  ======================================================== */

  /* ========================================================
     SMART LOCAL SERVICE INTENT
     --------------------------------------------------------
     IMPORTANT:
     The backend may rank a PURPOSE (for example scholarship or
     EWS) above the actual DOCUMENT the user is asking for.

     The frontend therefore detects explicit document requests first
     and uses that intent as a deterministic override.
  ======================================================== */
  const DOCUMENT_INTENTS = [
    {
      id: "income",
      aliases: [
        "income certificate",
        "income proof",
        "proof of income",
        "family income proof",
        "proof of family income",
        "family income certificate",
        "income document",
        "income verification",
        "salary proof",
        "earnings proof",
        "proof of my income",
        "proof of our income",
        "proof of annual income",
        "income proof for scholarship",
        "income certificate for scholarship",
        "income proof for college",
        "income certificate for college",
        "income proof for college admission",
        "income certificate for college admission",
        "income proof for admission",
        "income certificate for admission",
        "income proof for education",
        "income certificate for education",
        "income certificate for ews",
        "income proof for ews",
        "family income proof for scholarship",
        "family income certificate for scholarship",
        "family income proof for college",
      ],
      patterns: [
        /\bproof\s+of\s+(?:my\s+|our\s+|the\s+)?income\b/,
        /\bincome\s+proof\b/,
        /\bfamily\s+income\s+proof\b/,
        /\bproof\s+of\s+(?:my\s+|our\s+|the\s+)?family\s+income\b/,
        /\bincome\s+certificate\b/,
        /\bfamily\s+income\s+certificate\b/,
      ],
    },
    {
      id: "caste",
      aliases: [
        "caste certificate",
        "caste proof",
        "proof of caste",
        "community certificate",
        "community proof",
        "category certificate",
        "sc certificate",
        "st certificate",
        "obc certificate",
      ],
      patterns: [
        /\bproof\s+of\s+(?:my\s+|our\s+|the\s+)?caste\b/,
        /\bcaste\s+(?:proof|certificate|document)\b/,
        /\bcommunity\s+certificate\b/,
      ],
    },
    {
      id: "birth",
      aliases: [
        "birth certificate",
        "birth proof",
        "proof of birth",
        "birth document",
        "child birth certificate",
        "baby birth certificate",
        "newborn certificate",
      ],
      patterns: [
        /\bproof\s+of\s+(?:my\s+|the\s+)?birth\b/,
        /\bbirth\s+(?:proof|certificate|document)\b/,
      ],
    },
    {
      id: "death",
      aliases: [
        "death certificate",
        "death proof",
        "proof of death",
        "death document",
        "deceased certificate",
      ],
      patterns: [
        /\bproof\s+of\s+(?:the\s+)?death\b/,
        /\bdeath\s+(?:proof|certificate|document)\b/,
      ],
    },
    {
      id: "residence",
      aliases: [
        "residence certificate",
        "residence proof",
        "proof of residence",
        "address certificate",
        "address proof",
        "proof of address",
        "domicile certificate",
        "residential certificate",
      ],
      patterns: [
        /\bproof\s+of\s+(?:my\s+|the\s+)?(?:residence|address)\b/,
        /\b(?:residence|address)\s+(?:proof|certificate|document)\b/,
      ],
    },
    {
      id: "marriage",
      aliases: [
        "marriage certificate",
        "marriage registration",
        "marriage proof",
        "register marriage",
        "register my marriage",
        "wedding certificate",
      ],
      patterns: [
        /\bmarriage\s+(?:certificate|registration|proof|document)\b/,
      ],
    },
    {
      id: "disability",
      aliases: [
        "disability certificate",
        "disability proof",
        "proof of disability",
        "pwd certificate",
        "divyang certificate",
      ],
      patterns: [
        /\bproof\s+of\s+(?:my\s+|the\s+)?disability\b/,
        /\bdisability\s+(?:proof|certificate|document)\b/,
      ],
    },
    {
      id: "senior",
      aliases: [
        "senior citizen certificate",
        "senior citizen proof",
        "senior certificate",
        "elderly certificate",
      ],
      patterns: [
        /\bsenior\s+citizen\s+(?:proof|certificate|document)\b/,
      ],
    },
    {
      id: "ews",
      aliases: [
        "ews certificate",
        "ews proof",
        "economically weaker section certificate",
        "economically weaker section proof",
      ],
      patterns: [
        /\bews\s+(?:proof|certificate|document)\b/,
        /\beconomically\s+weaker\s+section\s+(?:proof|certificate|document)\b/,
      ],
    },
    {
      id: "vehicle",
      aliases: [
        "vehicle registration",
        "vehicle registration certificate",
        "registration certificate",
        "vehicle rc",
        "rc book",
        "car registration",
        "bike registration",
      ],
      patterns: [
        /\bvehicle\s+(?:registration|rc|certificate|document)\b/,
        /\bregistration\s+certificate\b/,
      ],
    },
    {
      id: "voter",
      aliases: [
        "voter id",
        "voter id card",
        "voter card",
        "electoral photo identity card",
        "epic card",
      ],
      patterns: [
        /\bvoter\s+(?:id|card|certificate|document)\b/,
      ],
    },
    {
      id: "aadhaar",
      aliases: [
        "aadhaar",
        "aadhar",
        "aadhaar card",
        "aadhar card",
        "uidai",
        "aadhaar document",
      ],
      patterns: [
        /\b(?:aadhaar|aadhar)\s+(?:card|document|proof)\b/,
      ],
    },
    {
      id: "pan",
      aliases: [
        "pan card",
        "pan",
        "permanent account number",
        "pan number",
      ],
      patterns: [
        /\bpan\s+(?:card|number|document|proof)\b/,
        /\bpermanent\s+account\s+number\b/,
      ],
    },
    {
      id: "passport",
      aliases: [
        "passport",
        "passport document",
        "passport application",
        "passport renewal",
      ],
      patterns: [
        /\bpassport\s+(?:application|document|renewal|proof)\b/,
      ],
    },
    {
      id: "driving",
      aliases: [
        "driving licence",
        "driving license",
        "learner licence",
        "learner license",
        "learning licence",
        "learning license",
        "driving licence document",
      ],
      patterns: [
        /\bdriving\s+(?:licence|license|document|proof)\b/,
        /\blearner\s+(?:licence|license)\b/,
      ],
    },
  ];

  const normalizeSearchText = (text) =>
    String(text || "")
      .toLowerCase()
      .replace(/schorlships/g, "scholarships")
      .replace(/scholorship/g, "scholarship")
      .replace(/scholarhsip/g, "scholarship")
      .replace(/certifcate/g, "certificate")
      .replace(/certficate/g, "certificate")
      .replace(/licencee/g, "licence")
      .replace(/[?.,!;:()\[\]{}]/g, " ")
      .replace(/\s+/g, " ")
      .trim();

  const detectRequestedServiceId = (query) => {
    const normalizedQuery = normalizeSearchText(query);
    if (!normalizedQuery) return null;

    // First: explicit phrases. These represent what the user is asking for.
    for (const intent of DOCUMENT_INTENTS) {
      if (intent.aliases.some((alias) => normalizedQuery.includes(alias))) {
        return intent.id;
      }
    }

    // Second: flexible patterns for natural language variations.
    for (const intent of DOCUMENT_INTENTS) {
      if (intent.patterns.some((pattern) => pattern.test(normalizedQuery))) {
        return intent.id;
      }
    }

    return null;
  };

  const getFrontendServiceById = (serviceId) => {
    if (!serviceId) return null;

    const serviceIdAliases = {
      income: ["income", "income-certificate", "income certificate"],
      caste: ["caste", "caste-certificate", "caste certificate"],
      birth: ["birth", "birth-certificate", "birth certificate"],
      death: ["death", "death-certificate", "death certificate"],
      residence: ["residence", "residence-certificate", "residence certificate"],
      marriage: ["marriage", "marriage-registration", "marriage registration", "marriage certificate"],
      disability: ["disability", "disability-certificate", "disability certificate"],
      senior: ["senior", "senior-citizen", "senior citizen", "senior citizen certificate"],
      ews: ["ews", "ews-certificate", "ews certificate"],
      vehicle: ["vehicle", "vehicle-registration", "vehicle registration"],
      voter: ["voter", "voter-id", "voter id", "voter card"],
      aadhaar: ["aadhaar", "aadhar", "aadhaar-card", "aadhaar card"],
      pan: ["pan", "pan-card", "pan card"],
      passport: ["passport"],
      driving: ["driving", "driving-licence", "driving license", "driving licence"],
    };

    const candidates = serviceIdAliases[serviceId] || [serviceId];

    return unifiedServices.find((service) => {
      const id = normalizeSearchText(service.id);
      const name = normalizeSearchText(service.name);
      return candidates.some((candidate) => {
        const normalizedCandidate = normalizeSearchText(candidate);
        return id === normalizedCandidate || name === normalizedCandidate;
      });
    }) || null;
  };

  const calculateFrontendConfidence = (score) =>
    Math.min(98, Math.max(65, Math.round(score * 1.2)));

  const calculateMatchScore = (query, service) => {
    const normalizedQuery = normalizeSearchText(query);
    if (!normalizedQuery || !service) return 0;

    const queryWords = normalizedQuery.split(/\s+/);
    let score = 0;

    const serviceName = normalizeSearchText(service.name);
    if (serviceName && normalizedQuery.includes(serviceName)) {
      score += 100;
    }

    (Array.isArray(service.keywords) ? service.keywords : []).forEach((keyword) => {
      const normalizedKeyword = normalizeSearchText(keyword);
      if (!normalizedKeyword) return;

      if (normalizedQuery.includes(normalizedKeyword)) {
        score += normalizedKeyword.includes(" ") ? 30 : 15;
      }

      normalizedKeyword.split(" ").forEach((word) => {
        if (word && queryWords.includes(word)) {
          score += 8;
        }
      });
    });

    const detectedId = detectRequestedServiceId(query);
    if (detectedId) {
      const candidate = getFrontendServiceById(detectedId);
      if (candidate && candidate === service) {
        score += 250;
      }
    }

    // Context/purpose words should never overpower an explicit document request.
    if (detectedId === "income") {
      if (normalizeSearchText(service.id) === "income") score += 100;
      if (normalizeSearchText(service.id) === "scholarship") score -= 180;
      if (normalizeSearchText(service.id) === "ews") score -= 100;
      if (normalizeSearchText(service.id) === "schemes") score -= 100;
    }

    return score;
  };

  const findBestService = (query) => {
    const serviceList = unifiedServices.length > 0 ? unifiedServices : services;
    const detectedId = detectRequestedServiceId(query);

    // Deterministic document-intent override.
    if (detectedId) {
      const requestedService = getFrontendServiceById(detectedId);
      if (requestedService) {
        return {
          service: requestedService,
          score: Math.max(300, calculateMatchScore(query, requestedService)),
          intentId: detectedId,
          deterministic: true,
        };
      }
    }

    return serviceList
      .map((service) => ({
        service,
        score: calculateMatchScore(query, service),
      }))
      .sort((a, b) => b.score - a.score)[0] || null;
  };

  /* ========================================================
     SEARCH
  ======================================================== */
  const findService = async () => {
    const text = search.trim();

    if (!text) {
      setSearchPerformed(true);
      setSelectedService(null);
      setMatchScore(0);
      return;
    }

    if (!requireLoginForSearch()) {
      return;
    }

    setSearchPerformed(true);
    setShowGuide(false);

    // Detect an explicit document request BEFORE accepting the backend ranking.
    // Example: "proof of my income for a government scholarship" must resolve
    // to Income Certificate; "scholarship" is only the purpose/context.
    const requestedIntentId = detectRequestedServiceId(text);
    const requestedFrontendService = getFrontendServiceById(requestedIntentId);

    // Step 3: use the SQLite/FastAPI smart-search endpoint first, but never
    // allow a purpose-only result to override an explicit document request.
    try {
      const selectedStateRecord = dbStates.find(
        (state) =>
          (state.name || "").trim().toLowerCase() ===
          selectedState.trim().toLowerCase()
      );

      const apiResults = await smartSearch(
        text,
        selectedStateRecord?.id ?? null
      );

      if (Array.isArray(apiResults) && apiResults.length > 0) {
        let best = apiResults[0];

        if (requestedIntentId) {
          const requestedNames = {
            income: ["income", "income certificate"],
            caste: ["caste", "caste certificate"],
            birth: ["birth", "birth certificate"],
            death: ["death", "death certificate"],
            residence: ["residence", "residence certificate"],
            marriage: ["marriage", "marriage registration", "marriage certificate"],
            disability: ["disability", "disability certificate"],
            senior: ["senior", "senior citizen", "senior citizen certificate"],
            ews: ["ews", "ews certificate"],
            vehicle: ["vehicle", "vehicle registration"],
            voter: ["voter", "voter id", "voter card"],
            aadhaar: ["aadhaar", "aadhar"],
            pan: ["pan", "pan card"],
            passport: ["passport"],
            driving: ["driving", "driving licence", "driving license"],
          };

          const wanted = requestedNames[requestedIntentId] || [requestedIntentId];
          const normalizedApiResults = apiResults.map((item) => ({
            item,
            name: normalizeSearchText(item.name),
          }));

          const intentMatch = normalizedApiResults.find(({ name }) =>
            wanted.some((wantedName) =>
              name === normalizeSearchText(wantedName) ||
              name.includes(normalizeSearchText(wantedName))
            )
          );

          if (intentMatch) {
            best = intentMatch.item;
          } else if (requestedFrontendService) {
            // Backend did not return the requested service, so use the
            // frontend's canonical service instead of showing the wrong one.
            setSelectedService(requestedFrontendService);
            setMatchScore(98);
            return;
          }
        }

        const databaseService = await loadServiceDetails(best.id);

        // Prefer the richer existing frontend service object when the
        // database service has the same name. This preserves icons,
        // keywords, mistakes and existing official-link behavior.
        const existingService = unifiedServices.find(
          (service) =>
            service.name?.trim().toLowerCase() ===
            best.name?.trim().toLowerCase()
        );

        const toArray = (value) => {
          if (Array.isArray(value)) return value;
          if (!value) return [];
          if (typeof value === "string") {
            try {
              const parsed = JSON.parse(value);
              return Array.isArray(parsed) ? parsed : [value];
            } catch {
              return value
                .split(/\r?\n|\s*;\s*/)
                .map((item) => item.trim())
                .filter(Boolean);
            }
          }
          return [];
        };

        const selectedStateRecordForMatch = dbStates.find(
          (state) =>
            state?.name?.trim().toLowerCase() ===
            selectedState?.trim().toLowerCase()
        );

        const selectedStateIdForMatch = Number(selectedStateRecordForMatch?.id);

        const stateSpecificDatabaseService =
          dbServices.find((item) => {
            const itemName = item?.name?.trim().toLowerCase();
            const itemStateId = Number(item?.state_id);

            return (
              itemName === best.name?.trim().toLowerCase() &&
              Number.isInteger(selectedStateIdForMatch) &&
              itemStateId === selectedStateIdForMatch
            );
          }) || databaseService;

        const matchedService = {
          ...(existingService || {}),
          ...(stateSpecificDatabaseService || {}),
          id:
            existingService?.id ||
            String(best.id ?? best.name)
              .toLowerCase()
              .replace(/[^a-z0-9]+/g, "-")
              .replace(/^-|-$/g, ""),
          name:
            databaseService?.name ||
            existingService?.name ||
            best.name ||
            "Government Service",
          icon: existingService?.icon || "🏛️",
          keywords:
            existingService?.keywords ||
            [best.name, best.category].filter(Boolean),
          mistakes: existingService?.mistakes || [],
          description:
            databaseService?.description ||
            existingService?.description ||
            best.description ||
            "Government service",
          eligibility:
            databaseService?.eligibility ||
            existingService?.eligibility ||
            best.eligibility ||
            "Check the official government portal for eligibility requirements.",
          documents:
            Array.isArray(databaseService?.documents) &&
            databaseService.documents.length > 0
              ? databaseService.documents
              : existingService?.documents ||
                (typeof best.documents === "string"
                  ? (() => {
                      try {
                        const parsed = JSON.parse(best.documents);
                        return Array.isArray(parsed) ? parsed : [best.documents];
                      } catch {
                        return [best.documents];
                      }
                    })()
                  : Array.isArray(best.documents)
                    ? best.documents
                    : []),
          steps:
            Array.isArray(databaseService?.steps) &&
            databaseService.steps.length > 0
              ? databaseService.steps
              : existingService?.steps ||
                (typeof best.steps === "string"
                  ? (() => {
                      try {
                        const parsed = JSON.parse(best.steps);
                        return Array.isArray(parsed) ? parsed : [best.steps];
                      } catch {
                        return [best.steps];
                      }
                    })()
                  : Array.isArray(best.steps)
                    ? best.steps
                    : []),
          fees:
            databaseService?.fees ||
            existingService?.fees ||
            best.fees ||
            "Check the official government portal for current fees.",
          processingTime:
            databaseService?.processingTime ||
            databaseService?.processing_time ||
            existingService?.processingTime ||
            best.processing_time ||
            "Processing time varies by service and authority.",
          officialPortalName:
            existingService?.officialPortalName ||
            stateSpecificDatabaseService?.officialPortalName ||
            stateSpecificDatabaseService?.official_portal_name ||
            "",
          officialPortalUrl:
            existingService?.officialPortalUrl ||
            stateSpecificDatabaseService?.officialPortalUrl ||
            stateSpecificDatabaseService?.official_portal_url ||
            "",
        };
        /* fallback object retained through the merged object above */
        if (!matchedService.name) {
          matchedService.name = best.name || "Government Service";
        }


        matchedService.documents = Array.isArray(matchedService.documents)
          ? matchedService.documents
          : toArray(matchedService.documents);

        matchedService.steps = Array.isArray(matchedService.steps)
          ? matchedService.steps
          : toArray(matchedService.steps);

        setSelectedService(matchedService);
        setMatchScore(
          Math.min(98, Math.max(65, Math.round((best.match_score || 0) * 1.2)))
        );
        return;
      }
    } catch (error) {
      console.warn(
        "Smart search unavailable. Using local search fallback:",
        error
      );
    }

    // Existing local search remains untouched as a fallback.
    const result = findBestService(text);

    if (!result || result.score < 15) {
      setSelectedService({
        id: "not-found",
        name: "No service found",
        icon: "🔎",
        description:
          "We couldn't confidently identify a government service from your request.",
      });

      setMatchScore(0);
      return;
    }

    const confidence = Math.min(
      98,
      Math.max(65, Math.round(result.score * 1.2))
    );

    setSelectedService(result.service);
    setMatchScore(confidence);
  };

  /* ========================================================
     OPEN GUIDE
  ======================================================== */

  const openGuide = (service) => {
    setSelectedService(service);
    setShowGuide(true);
    setSearchPerformed(true);

    setTimeout(() => {
      document.getElementById("service-guide")?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }, 100);
  };

  /* ========================================================
     SUGGESTIONS
  ======================================================== */

  const suggestions = [
    "I need proof of my family income",
    "I want a caste certificate",
    "I have a newborn baby",
    "I need a death certificate",
    "I want to apply for PAN",
    "I need Aadhaar update",
    "I need a residence certificate",
    "I want to register my marriage",
    "I need a driving licence",
    "I want a voter ID",
    "I need a ration card",
    "I need an EWS certificate",
    "I want a scholarship",
    "I need vehicle registration",
    "I need a disability certificate",
    "I want PM Kisan",
    "I need a government job",
    "I need pension or social security support",
  ];

  const useSuggestion = (suggestion) => {
    setSearch(suggestion);

    const result = findBestService(suggestion);

    if (result && result.score >= 15) {
      setSelectedService(result.service);
      setMatchScore(
        Math.min(98, Math.max(65, Math.round(result.score * 1.2)))
      );
      setSearchPerformed(true);
      setShowGuide(false);
    }
  };

  /* ========================================================
     AI
  ======================================================== */

  const openAI = () => setShowAI(true);

  const closeAI = () => setShowAI(false);

  const formatAIResponse = (rawResponse) => {
    try {
      return {
        type: "structured",
        data: JSON.parse(rawResponse),
      };
    } catch {
      return {
        type: "text",
        data: rawResponse,
      };
    }
  };

  const sendAIMessage = async () => {
    const userInput = aiInput.trim();

    if (!userInput || aiLoading) return;

    if (!sessionId) {
      console.error("Session ID is not available yet.");
      return;
    }

    setMessages((previous) => [
      ...previous,
      {
        role: "user",
        content: userInput,
      },
    ]);

    setAiInput("");
    setAiLoading(true);

    try {
      const data = await sendChatMessage(userInput, sessionId);

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: formatAIResponse(data.response),
        },
      ]);
    } catch (error) {
      console.error("AI Error:", error);

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: {
            type: "text",
            data:
              "⚠️ I couldn't connect to the AI server. Please make sure FastAPI is running on port 8000.",
          },
        },
      ]);
    } finally {
      setAiLoading(false);
    }
  };

  const handleAIKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendAIMessage();
    }
  };

  const clearAIChat = () => {
    setMessages([
      {
        role: "assistant",
        content:
          "Namaste! 🇮🇳 I'm GovNavigator AI. Tell me what government service you need and I'll help you understand the possible service, documents and next steps.",
      },
    ]);
  };

  /* ========================================================
     AI RESPONSE UI
  ======================================================== */

  const renderAIContent = (content) => {
    if (!content) return null;

    if (typeof content === "string") {
      return <div className="plain-ai-response">{content}</div>;
    }

    if (content.type !== "structured") {
      return (
        <div className="plain-ai-response">
          {content.data || content}
        </div>
      );
    }

    const data = content.data || {};

    return (
      <div className="structured-ai-response">
        <div className="ai-recommendation">
          <div className="ai-card-icon">🎯</div>

          <div>
            <small>RECOMMENDED SERVICE</small>
            <h3>{data.service_name || "Government Service"}</h3>
          </div>
        </div>

        {data.recommendation && (
          <div className="ai-info-card">
            <h4>💡 Recommendation</h4>
            <p>{data.recommendation}</p>
          </div>
        )}

        {data.why && (
          <div className="ai-info-card">
            <h4>❓ Why this service?</h4>
            <p>{data.why}</p>
          </div>
        )}

        {Array.isArray(data.documents) &&
          data.documents.length > 0 && (
            <div className="ai-info-card">
              <h4>📄 Common Documents</h4>

              <ul>
                {data.documents.map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            </div>
          )}

        {Array.isArray(data.steps) &&
          data.steps.length > 0 && (
            <div className="ai-info-card">
              <h4>📝 General Steps</h4>

              <ol>
                {data.steps.map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ol>
            </div>
          )}

        {data.important_note && (
          <div className="ai-important">
            <h4>⚠️ Important</h4>
            <p>{data.important_note}</p>
          </div>
        )}

        {data.disclaimer && (
          <div className="ai-disclaimer-box">
            {data.disclaimer}
          </div>
        )}
      </div>
    );
  };

  /* ========================================================
     JSX
  ======================================================== */

  return (
    <div className="app">
      {/* NAVBAR */}

      <nav className="navbar">
        <div className="logo">
          <img className="india-flag" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAiMAAAFtCAIAAABa8v1nAAAQAElEQVR4AeydCXxU1dn/D0lgWANKUECEAFUEBKu+hEowKurfJXELLtWqJFVxQSUtKGKrBG1FFNqg4oLaBLW4ErdE7auiRoIFXrWCgGiBsCgoQSHIEkjk/517w+RmZhImQDJ3Jr/3c7w59znPeZbv6Xue3HsmQ8yeGxLVREAEREAERKDhCMQY/Z8IiIAIiIAINCQBVZqGpCvb0URAuYiACOwvAVWa/SWneSIgAiIgAqERUKUJjZO0REAEREAEQiMQqKVKE8hEEhEQAREQgYNJQJXmYNKULREQAREQgUACqjSBTCQRAWPEQARE4OARUKU5eCxlSQREQAREIBgBVZpgVCQTAREQAREIjUAoWqo0oVCSjgiIgAiIwP4TUKXZf3aaKQIiIAIiEAoBVZpQKEkn2gkoPxEQgYYkoErTkHRlWwREQAREwBhVGv2vQAREQAREIFQC+6enSrN/3DRLBERABEQgVAKqNKGSkp4IiIAIiMD+EVCl2T9umhXJBBS7CIhA4xJQpWlc3vImAiIgAk2PgCpN01tzZSwCIiACoRE4WFqqNAeLpOyIgAiIgAgEJ6BKE5yLpCIgAiIgAgeLgCrNwSIpO24loLhEQATCTUCVJtwrIP8iIAIiEO0EVGmifYWVnwiIgAiERqDhtFRpGo6tLIuACIiACHgJqNJ4Keg/ERABERCBhiOgStNwbGU5HATkUwREwH0EVGnctyaKSAREQASii4AqTXStp7IRAREQgdAINKaWKk1j0pYvERABEWiKBFRpmuKqK2cREAERaEwCqjSNSVu+DjYB2RMBEYgEAqo0kbBKilEEREAEIpmAKk0kr55iFwEREIHQCIRXS5UmvPzlXQREQASin4AqTfSvsTIUAREQgfASUKUJL395rw8B6YqACEQmAVWayFw3RS0CIiACkUNAlSZy1kqRioAIiEBoBNympUrjthVRPCIgAiIQbQRUaaJtRZWPCIiACLiNgCqN21ZE8ewloJ8iIALRQkCVJlpWUnmIgAiIgFsJqNK4dWUUlwiIgAiERsD9Wqo07l8jRSgCIiACkU1AlSay10/Ri4AIiID7CajSuH+NmkaEylIERCB6CajSRO/aKjMREAERcAcBVRp3rIOiEAEREIHQCESilipNJK6aYhYBERCBSCKgShNJq6VYRUAERCASCajSROKqRX7MykAERKApEVClaUqrrVxFQAREIBwEVGnCQV0+RUAERCA0AtGhpUoTHeuoLERABETAvQRUady7NopMBERABKKDgCpNdKyju7NQdCIgAk2bgCpN015/ZS8CIiACDU9AlabhGcuDCIiACIRGIFq1VGmidWWVlwiIgAi4hYAqjVtWQnGIgAiIQLQSUKWJ1pUNX17yLAIiIAI1CajS1OShOxEQAREQgYNNQJXmYBOVPREQAREIjUDT0VKlaTprrUxFQAREIDwEVGnCw11eRUAERKDpEFClaTpr3TCZyqoIiIAI7IuAKs2+CGlcBERABETgwAio0hwYP80WAREQgdAINGUtVZqmvPrKXQREQAQag4AqTWNQlg8REAERaMoEVGma8urXP3fNEAEREIH6E1ClqT8zzRABERABEagPAVWa+tCSrgiIgAiERkBaTgKqNE4a6ouACIiACBx8Aqo0B5+pLIqACIiACDgJqNI4aahfk4DuREAEROBgEFClORgUZUMEREAERKB2Aqo0tbPRiAiIgAiERkBadRNQpambj0ZFQAREQAQOlIAqzYES1HwREAEREIG6CajS1M2nKY0qVxEQARFoGAKqNA3DVVZFQAREQAT2ElCl2UtCP0VABEQgNALSqi8BVZr6EpO+CIiACIhA/Qio0tSPl7RFQAREQATqS0CVpr7EokVfeYiACIhAYxFQpWks0vIjAiIgAk2VgCpNU1155S0CIhAaAWkdOAFVmgNnKAsiIAIiIAJ1EVClqYuOxkRABERABA6cgCrNgTOMBAuKUQREQATCR0CVJnzs5VkEREAEmgYBVZqmsc7KUgREIDQC0moIAqo0DUFVNkVABERABKoJqNJUs1BPBERABESgIQio0jQE1XDblH8REAERcBMBVRo3rYZiEQEREIFoJKBKE42rqpxEQARCIyCtxiGgStM4nOVFBERABJouAVWaprv2ylwEREAEGoeAKk3jcG5IL7ItAiIgAu4moErj7vVRdCIgAiIQ+QRUaSJ/DZWBCIhAaASkFS4CqjThIi+/IiACItBUCKjSNJWVVp4iIAIiEC4CqjThIr+/fjVPBERABCKNgCpNpK2Y4hUBERCBSCOgShNpK6Z4RUAEQiMgLfcQUKVxz1ooEhEQARGITgKqNNG5rspKBERABNxDQJXG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NwzBDtaw2STYKUkR2BcBVZp9EdJ40yDgyzIuLoaD+m7dOtA4UElN7c9Dye23D3twSlpu3mUvvnS53egjQc4oOmiiT2Mur+Z81tQRARGAgCoNENREQAREQAQakIAqTQPClWkREAERiDoC+5OQKs3+UNMcERABERCB0AnE3PrURDUREAEREAERaDgCMQ/Pe0FNBJoaAeUrAiLQmARi4lp1UBMBERABERCBhiOgc5rQ3zRKUwREQASaGoGDk68qzcHhKCsiIAIiIAK1EVClqY2M5CIgAiIgAgeHgCrNweEoK24moNhEQATCS0CVJrz85V0EREAEop+AKk30r7EyFAEREIHQCDSUlipNQ5GVXREQAREQAZuAKo3NQVcREAEREIGGIqBK01BkZTdcBORXBETAbQRUady2IopHBERABKKNgCpNtK2o8hEBERCB0Ag0npYqTeOxlicREAERaJoEVGma5roraxEQARFoPAKqNI3HWp4agoBsioAIuJ+AKo3710gRioAIiEBkE1Cliez1U/QiIAIiEBqBcGqp0oSTvnyLgAiIQFMgoErTFFZZOYqACIhAOAmo0oSTvnzXl4D0RUAEIpGAKk0krppiFgEREIFIIqBKE0mrpVhFQAREIDQC7tJSpXHXeigaERABEYg+Aqo00bemykgEREAE3EVAlcZd66FonATUFwERiA4CqjTRsY7KQgREQATcS0CVxr1ro8hEQAREIDQCbtdSpXH7Cik+ERABEYh0Aqo0kb6Cil8EREAE3E5AlcbtK9R04lOmIiAC0UpAlSZaV1Z5iYAIiIBbCKjSuGUlFIcIiIAIhEYg8rRUaSJvzRSxCIiACEQWAVWayFovRSsCIiACkUdAlSby1iw6IlYWIiACTYeAKk3TWWtlKgIiIALhIaBKEx7u8ioCIiACoRGIBi1VmmhYReUgAiIgAm4moErj5tVRbCIgAiIQDQRUaaJhFd2fgyIUARFoygRUaZry6it3ERABEWgMAqo0jUFZPkRABEQgNALRqaVKE53rqqxEQAREwD0EVGncsxaKRAREQASik4AqTXSua3izkncREAERcBJQpXHSUF8EREAERODgE1ClOfhMZVEEREAEQiPQVLRUaZrKSitPERABEQgXAVWacJGXXxEQARFoKgRUaZrKSjdcnrIsAiIgAnUTUKWpm49GRUAEREAEDpSAKs2BEtR8ERABEQiNQNPVUqVpumuvzEVABESgcQio0jQOZ3kRAREQgaZLQJWm6a79/mWuWSIgAiJQXwKqNPUlJn0REAEREIH6EVClqR8vaYuACIhAaASkVU1AlaaahXoiIAIiIAINQUCVpiGoyqYIiIAIiEA1AVWaahbqBRKQRAREQAQOnIAqzYEzlAUREAEREIG6CKjS1EVHYyIgAiIQGgFp1UVAlaYuOhoTAREQARE4cAKqNAfOUBZEQAREQATqIqBKUxedpjamfEVABESgIQio0jQEVdkUAREQARGoJqBKU81CPREQAREIjYC06kdAlaZ+vKQtAiIgAiJQXwKqNPUlJn0REAEREIH6EVClqR+vaNJWLiIgAiLQOARUaRqHs7yIgAiIQNMloErTdNdemYuACIRGQFoHSkCV5kAJar4IiIAIiEDdBFRp6uajUREQAREQgQMloEpzoAQjZb7iFAEREIFwEVClCRd5+RUBERCBpkJAlaaprLTyFAERCI2AtA4+AVWag89UFkVABERABJwEVGmcNNQXAREQARE4+ARUaQ4+UzdYVAwiIAIi4B4CqjTuWQtFIgIiIALRSUCVJjrXVVmJgAiERkBajUFAlaYxKMuHCIiACDRlAqo0TXn1lbsIiIAINAYBVZrGoNzQPmRfBERABNxMQJXGzauj2ERABEQgGgio0kTDKioHERCB0AhIKzwEVGnCw11eRUAERKDpEFClaTprrUxFQAREIDwEVGnCw/1AvGquCIiACEQWAVWayFovRSsCIiACkUdAlSby1kwRi4AIhEZAWm4hoErjlpVQHCIgAiIQrQRUaaJ1ZZWXCIiACLiFgCqNW1aitjgkFwEREIFIJ6BKE+krqPhFQAREwO0EVGncvkKKTwREIDQC0nIvAVUa966NIhMBERCB6CCgShMd66gsREAERMC9BFRp3LU2ikYEREAEoo+AKk30rakyEgEREAF3EVClcdd6KBoREIHQCEgrkgio0kTSailWERABEYhEAqo0kbhqilkEREAEIomAKk04V0u+RUAERKApEFClaQqrrBxFQAREIJwEVGnCSV++RUAEQiMgrcgmoEoT2eun6EVABETA/QRUady/RopQBERABCKbgCpN462fPImACIhA0ySgStM0111Zi4AIiEDjEVClaTzW8iQCIhAaAWlFGwFVmmhbUeUjAiIgAm4joErjthVRPCIgAiIQbQRUaRpqRWVXBERABETAJqBKY3PQVQREQAREoKEIqNI0FFnZFQERCI2AtKKfgCpN9K+xMhQBERCB8BJQpQkvf3kXAREQgegnoEpzcNZYVkRABERABGoj8P8BAAD//xCOiEQAAAAGSURBVAMARyo5XZ4laC8AAAAASUVORK5CYII=" alt="Indian flag" />
          <span>GovNavigator</span>
        </div>

        <button
          type="button"
          className="sound-toggle"
          aria-label={soundEnabled ? "Mute sound effects" : "Enable sound effects"}
          title={soundEnabled ? "Mute sound effects" : "Enable sound effects"}
          onClick={() => setSoundEnabled((enabled) => !enabled)}
        >
          {soundEnabled ? "🔊" : "🔇"}
        </button>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "10px",
            flexWrap: "wrap",
            justifyContent: "flex-end",
          }}
        >
          {currentUser ? (
            <>
              <span
                style={{
                  fontWeight: 600,
                  fontSize: "14px",
                  padding: "8px 12px",
                  borderRadius: "999px",
                  background: "#f1f5f9",
                  color: "#0f172a",
                }}
              >
                👋 {currentUser.name}
              </span>

              <button
                type="button"
                onClick={handleLogout}
                style={{
                  border: "1px solid #cbd5e1",
                  background: "#ffffff",
                  color: "#0f172a",
                  borderRadius: "10px",
                  padding: "9px 14px",
                  cursor: "pointer",
                  fontWeight: 600,
                }}
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                onClick={openLogin}
                style={{
                  border: "1px solid #cbd5e1",
                  background: "#ffffff",
                  color: "#0f172a",
                  borderRadius: "10px",
                  padding: "9px 14px",
                  cursor: "pointer",
                  fontWeight: 600,
                }}
              >
                Login
              </button>

              <button
                type="button"
                onClick={openRegister}
                style={{
                  border: "none",
                  background: "#0f172a",
                  color: "#ffffff",
                  borderRadius: "10px",
                  padding: "9px 14px",
                  cursor: "pointer",
                  fontWeight: 600,
                }}
              >
                Register
              </button>
            </>
          )}

          <button className="ai-nav-button" onClick={openAI}>
            🤖 Ask AI
          </button>
          {currentUser && (
  <>
    <button
      className="ai-nav-button"
      onClick={() => {
        setShowSearchHistory(true);
        loadSearchHistory();
      }}
    >
      📜 Search History
    </button>

    <button
      className="ai-nav-button"
      onClick={() => {
        setShowFavorites(true);
        loadFavorites();
      }}
    >
      ⭐ Saved Services ({favorites.length})
    </button>
  </>
)}
        </div>
      </nav>


      {/* HERO */}

      <main className="hero">
        <div className="hero-content">
          <p className="badge">
            🇮🇳 Government services, made simple
          </p>

          <h1>
            Find the right government service
            <span> without the confusion.</span>
          </h1>

          <p className="subtitle">
            Select your state, describe what you need and
            GovNavigator helps you understand the service,
            documents, process and application portal.
          </p>

          {/* STATE */}

          <div className="state-selector">
            <label htmlFor="state">
              📍 Select your State / Union Territory
            </label>

            <input
              id="state"
              list="govnavigator-states"
              value={selectedState}
              onChange={(event) => {
                setSelectedState(event.target.value);
                setSelectedService(null);
                setShowGuide(false);
                setSearchPerformed(false);
              }}
              placeholder="Type or select your state / UT"
              autoComplete="off"
              style={{ width: "100%", boxSizing: "border-box" }}
            />
            <datalist id="govnavigator-states">
              {(dbStates.length > 0 ? dbStates : states).map((state) => (
                <option
                  key={state.id || state}
                  value={state.name || state}
                />
              ))}
            </datalist>
          </div>

          {/* SEARCH */}

          <div className="search-box">
            <span>🔍</span>

            <input
              type="text"
              placeholder="Example: I need proof of my family income"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  findService();
                }
              }}
            />

            <button onClick={findService}>
              Find My Service
            </button>
          </div>

          {/* SUGGESTIONS */}

          <div className="search-suggestions">
            <span>Try:</span>

            {suggestions.map((suggestion) => (
              <button
                key={suggestion}
                onClick={() => useSuggestion(suggestion)}
              >
                {suggestion}
              </button>
            ))}
          </div>

          {/* SEARCH RESULT */}

          {searchPerformed && selectedService && (
            <div className="result-box">
              {selectedService.id === "not-found" ? (
                <>
                  <p>
                    🔎 We couldn't confidently identify a service.
                  </p>

                  <h3>Try describing what you need</h3>

                  <p>
                    Example: "I need proof of my income"
                    or "I need a birth certificate."
                  </p>
                </>
              ) : (
                <>
                  <div className="result-header">
                    <div style={{ flex: 1 }}>
  <p>🎯 Best matching service</p>

  <h3>
    {selectedService.icon}{" "}
    {selectedService.name}
  </h3>

  {selectedState && (
    <div className="selected-state-badge">
      📍 Recommended for {selectedState}
    </div>
  )}
</div>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "12px",
                      }}
                    >
                      <button
                        type="button"
                        onClick={() => toggleFavorite(selectedService)}
                        disabled={
                          favoriteLoadingId ===
                          getDatabaseServiceId(selectedService)
                        }
                        title={
                          isServiceFavorite(selectedService)
                            ? "Remove from saved services"
                            : "Save this service"
                        }
                        style={{
                          border: "1px solid #cbd5e1",
                          background: "#ffffff",
                          borderRadius: "10px",
                          padding: "8px 11px",
                          cursor: "pointer",
                          fontSize: "18px",
                          lineHeight: 1,
                        }}
                      >
                        {isServiceFavorite(selectedService) ? "⭐" : "☆"}
                      </button>

                      <div className="confidence">
                        <strong>{matchScore}%</strong>
                        <span>Match</span>
                      </div>
                    </div>
                  </div>

                  <p>{selectedService.description}</p>

                  <button
                    onClick={() =>
                      openGuide(selectedService)
                    }
                  >
                    View Service Guide →
                  </button>
                </>
              )}
            </div>
          )}
        </div>
      </main>

      {/* SERVICE GUIDE */}

      {showGuide &&
        selectedService &&
        selectedService.id !== "not-found" && (
          <section
            className="guide-section"
            id="service-guide"
          >
            <p className="small-title">
              SERVICE GUIDE
            </p>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: "16px",
                flexWrap: "wrap",
              }}
            >
              <h2 style={{ marginBottom: 0 }}>
                {selectedService.icon}{" "}
                {selectedService.name}
              </h2>

              <button
                type="button"
                onClick={() => toggleFavorite(selectedService)}
                disabled={
                  favoriteLoadingId ===
                  getDatabaseServiceId(selectedService)
                }
                style={{
                  border: "1px solid #cbd5e1",
                  background: "#ffffff",
                  color: "#0f172a",
                  borderRadius: "10px",
                  padding: "9px 14px",
                  cursor: "pointer",
                  fontWeight: 700,
                }}
              >
                {isServiceFavorite(selectedService)
                  ? "⭐ Saved"
                  : "☆ Save Service"}
              </button>
            </div>

            {selectedState && (
  <div className="selected-state-badge">
    📍 Service information for {selectedState}
  </div>
)}

            <p className="guide-description">
              {selectedService.description}
            </p>

            <div className="guide-grid">
              <div className="guide-card">
                <h3>👤 Eligibility</h3>
                <p>{selectedService.eligibility}</p>
              </div>

              <div className="guide-card">
                <h3>📄 Documents Required</h3>

                <ul>
                  {selectedService.documents.map(
                    (document, index) => (
                      <li key={index}>{document}</li>
                    )
                  )}
                </ul>
              </div>

              <div className="guide-card">
                <h3>📝 How to Apply</h3>

                <ol>
                  {selectedService.steps.map(
                    (step, index) => (
                      <li key={index}>{step}</li>
                    )
                  )}
                </ol>
              </div>

              <div className="guide-card">
                <h3>⚠️ Common Mistakes</h3>

                <ul>
                  {selectedService.mistakes.map(
                    (mistake, index) => (
                      <li key={index}>{mistake}</li>
                    )
                  )}
                </ul>
              </div>

              <div className="guide-card">
                <h3>💰 Fees</h3>
                <p>{selectedService.fees}</p>
              </div>

              <div className="guide-card">
                <h3>⏱️ Processing Time</h3>
                <p>{selectedService.processingTime}</p>
              </div>
            </div>

            {/* APPLICATION PORTAL */}

            <div className="official-info">
              <h3>🌐 Application Portal</h3>

              {!selectedState ? (
                <div className="portal-warning">
                  <p>
                    📍 Select your state above to see the
                    applicable application portal.
                  </p>
                </div>
              ) : (
                <>
                  <p>
                    Apply for{" "}
                    <strong>
                      {selectedService.name}
                    </strong>{" "}
                    in <strong>{selectedState}</strong>.
                  </p>

                  {getServiceLink(selectedService) ? (
                    <div className="portal-card">
                      <div>
                        <span className="portal-label">
                          OFFICIAL SERVICE PORTAL
                        </span>

                        <h4>
                          {
                            getServiceLink(
                              selectedService
                            ).name
                          }
                        </h4>
                      </div>

                      <a
                        href={
                          getServiceLink(
                            selectedService
                          ).url
                        }
                        target="_blank"
                        rel="noopener noreferrer"
                        className="apply-button"
                      >
                        Apply Now ↗
                      </a>
                    </div>
                  ) : (
                    <div className="portal-warning">
                      <p>
                        The exact online route could not
                        be confidently mapped for this
                        state/service yet.
                      </p>

                      <p>
                        Please use the official state
                        government service directory.
                      </p>
                    </div>
                  )}

                  <p className="official-note">
                    🔐 GovNavigator is an independent
                    prototype. Always verify the current
                    requirements, documents, fees and
                    procedure on the official government
                    portal before submitting an application.
                  </p>
                </>
              )}
            </div>
          </section>
        )}

      {/* POPULAR SERVICES */}

      <section className="services">
        <div className="section-heading">
          <div>
            <p className="small-title">
              EXPLORE SERVICES
            </p>

            <h2>
              Popular Government Services
            </h2>
          </div>

          <p>
            Select a service to explore its eligibility,
            documents, process and application route.
          </p>
        </div>

        <div className="service-grid">
          {(unifiedServices.length > 0 ? unifiedServices : services).map(
            (service) => (
              <div
                className="service-card"
                key={service.id}
                style={{ position: "relative" }}
              >
              <button
                type="button"
                onClick={(event) => {
                  event.stopPropagation();
                  toggleFavorite(service);
                }}
                disabled={
                  favoriteLoadingId === getDatabaseServiceId(service)
                }
                title={
                  isServiceFavorite(service)
                    ? "Remove from saved services"
                    : "Save this service"
                }
                style={{
                  position: "absolute",
                  top: "12px",
                  right: "12px",
                  border: "1px solid #cbd5e1",
                  background: "#ffffff",
                  borderRadius: "9px",
                  width: "38px",
                  height: "38px",
                  cursor: "pointer",
                  fontSize: "18px",
                  lineHeight: 1,
                  zIndex: 2,
                }}
              >
                {isServiceFavorite(service) ? "⭐" : "☆"}
              </button>

              <div className="service-icon">
                {service.icon}
              </div>

              <h3>{service.name}</h3>

              <p>{service.description}</p>

              <button
                onClick={() => openGuide(service)}
              >
                Explore →
              </button>
              </div>
            )
          )}
        </div>
      </section>
     {/* ============================================================
    SEARCH ANALYTICS DASHBOARD
    ============================================================ */}

<section className="analytics-dashboard">

  <div className="analytics-header">

    <div>
      <h2>📊 Search Analytics</h2>

      <p>
        Insights from GovNavigator user searches
      </p>
    </div>

    <button
      className="analytics-refresh-btn"
      onClick={loadAnalytics}
      disabled={analyticsLoading}
    >
      {analyticsLoading
        ? "Refreshing..."
        : "↻ Refresh"}
    </button>

  </div>


  {analyticsError && (
    <div className="analytics-error">
      {analyticsError}
    </div>
  )}


  {analyticsLoading && !analytics && (
    <div className="analytics-loading">
      Loading analytics...
    </div>
  )}


  {analytics && (
    <>
      {/* --------------------------------------------------------
          SUMMARY CARDS
          -------------------------------------------------------- */}

      <div className="analytics-cards">

        <div className="analytics-card">
          <div className="analytics-card-icon">
            🔎
          </div>

          <div>
            <span>Total Searches</span>

            <strong>
              {analytics.summary.total_searches}
            </strong>
          </div>
        </div>


        <div className="analytics-card">
          <div className="analytics-card-icon">
            ✅
          </div>

          <div>
            <span>Successful</span>

            <strong>
              {analytics.summary.successful_searches}
            </strong>
          </div>
        </div>


        <div className="analytics-card">
          <div className="analytics-card-icon">
            ❌
          </div>

          <div>
            <span>Failed</span>

            <strong>
              {analytics.summary.failed_searches}
            </strong>
          </div>
        </div>


        <div className="analytics-card">
          <div className="analytics-card-icon">
            📈
          </div>

          <div>
            <span>Success Rate</span>

            <strong>
              {analytics.summary.success_rate}%
            </strong>
          </div>
        </div>


        <div className="analytics-card">
          <div className="analytics-card-icon">
            🎯
          </div>

          <div>
            <span>Avg Match Score</span>

            <strong>
              {analytics.summary.average_match_score}
            </strong>
          </div>
        </div>

      </div>


      {/* --------------------------------------------------------
          ANALYTICS TABLES
          -------------------------------------------------------- */}

      <div className="analytics-grid">


        {/* TOP QUERIES */}

        <div className="analytics-panel">

          <h3>🔥 Popular Searches</h3>

          {analytics.top_queries.length === 0 ? (

            <p className="analytics-empty">
              No search data yet.
            </p>

          ) : (

            <div className="analytics-list">

              {analytics.top_queries.map(
                (item, index) => (

                  <div
                    className="analytics-list-item"
                    key={`${item.query}-${index}`}
                  >

                    <span className="analytics-rank">
                      #{index + 1}
                    </span>

                    <span className="analytics-name">
                      {item.query}
                    </span>

                    <span className="analytics-count">
                      {item.count}
                    </span>

                  </div>

                )
              )}

            </div>

          )}

        </div>


        {/* TOP SERVICES */}

        <div className="analytics-panel">

          <h3>🏛️ Popular Services</h3>

          {analytics.top_services.length === 0 ? (

            <p className="analytics-empty">
              No service data yet.
            </p>

          ) : (

            <div className="analytics-list">

              {analytics.top_services.map(
                (item, index) => (

                  <div
                    className="analytics-list-item"
                    key={`${item.service}-${index}`}
                  >

                    <span className="analytics-rank">
                      #{index + 1}
                    </span>

                    <span className="analytics-name">
                      {item.service}
                    </span>

                    <span className="analytics-count">
                      {item.count}
                    </span>

                  </div>

                )
              )}

            </div>

          )}

        </div>


        {/* TOP STATES */}

        <div className="analytics-panel">

          <h3>📍 Popular States</h3>

          {analytics.top_states.length === 0 ? (

            <p className="analytics-empty">
              No state data yet.
            </p>

          ) : (

            <div className="analytics-list">

              {analytics.top_states.map(
                (item, index) => (

                  <div
                    className="analytics-list-item"
                    key={`${item.state}-${index}`}
                  >

                    <span className="analytics-rank">
                      #{index + 1}
                    </span>

                    <span className="analytics-name">
                      {item.state}
                    </span>

                    <span className="analytics-count">
                      {item.count}
                    </span>

                  </div>

                )
              )}

            </div>

          )}

        </div>


        {/* RECENT SEARCHES */}

        <div className="analytics-panel analytics-recent-panel">

          <h3>🕐 Recent Searches</h3>

          {analytics.recent_searches.length === 0 ? (

            <p className="analytics-empty">
              No recent searches.
            </p>

          ) : (

            <div className="analytics-recent-list">

              {analytics.recent_searches.map(
                (item) => (

                  <div
                    className="analytics-recent-item"
                    key={item.id}
                  >

                    <div>

                      <strong>
                        {item.query}
                      </strong>

                      {item.service && (
                        <span>
                          {item.service}
                        </span>
                      )}

                    </div>

                    <div className="analytics-score">

                      {item.match_score ?? 0}

                    </div>

                  </div>

                )
              )}

            </div>

          )}

        </div>

      </div>

    </>
  )}

</section>
      {/* AI SECTION */}

      <section className="ai-section">
        <div>
          <p className="small-title">
            AI ASSISTANT
          </p>

          <h2>
            Not sure what service you need?
          </h2>

          <p>
            Describe your situation in normal language.
            GovNavigator AI can help identify the
            government service that may be relevant.
          </p>
        </div>

        <button
          className="ai-main-button"
          onClick={openAI}
        >
          🤖 Ask GovNavigator AI
        </button>
      </section>

      {/* FOOTER */}

      <footer>
        <p>
          🇮🇳 GovNavigator is an independent prototype
          and is not an official government website.
        </p>
      </footer>

      {/* AI CHAT */}

      {showAI && (
        <div className="ai-overlay">
          <div className="ai-chat">
            <div className="ai-chat-header">
              <div>
                <div className="ai-chat-title">
                  🤖 GovNavigator AI
                </div>

                <div className="ai-chat-status">
                  ● AI Assistant
                </div>
              </div>

              <div className="ai-chat-actions">
                <button
                  onClick={clearAIChat}
                  title="Clear conversation"
                >
                  ↻
                </button>

                <button
                  onClick={closeAI}
                  title="Close"
                >
                  ✕
                </button>
              </div>
            </div>

            <div className="ai-chat-messages">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`ai-message ${
                    message.role === "user"
                      ? "user-message"
                      : "assistant-message"
                  }`}
                >
                  <div className="message-avatar">
                    {message.role === "user"
                      ? "👤"
                      : "🤖"}
                  </div>

                  <div className="message-content">
                    {message.role === "assistant"
                      ? renderAIContent(message.content)
                      : message.content}
                  </div>
                </div>
              ))}

              {aiLoading && (
                <div className="ai-message assistant-message">
                  <div className="message-avatar">
                    🤖
                  </div>

                  <div className="message-content typing">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              )}
            </div>

            <div className="ai-quick-actions">
              <button
                onClick={() =>
                  setAiInput(
                    "Which government certificate should I get if I need to prove my income?"
                  )
                }
              >
                💰 Income certificate
              </button>

              <button
                onClick={() =>
                  setAiInput(
                    "What documents are usually needed for a caste certificate?"
                  )
                }
              >
                📜 Caste certificate
              </button>

              <button
                onClick={() =>
                  setAiInput(
                    "I have a newborn baby. What government document should I get?"
                  )
                }
              >
                👶 Newborn
              </button>

              <button
                onClick={() =>
                  setAiInput(
                    "How can I apply for a driving licence?"
                  )
                }
              >
                🚗 Driving licence
              </button>

              <button
                onClick={() =>
                  setAiInput(
                    "How can I register as a voter?"
                  )
                }
              >
                🗳️ Voter ID
              </button>

              <button
                onClick={() =>
                  setAiInput(
                    "Which government scholarship can I apply for?"
                  )
                }
              >
                🎓 Scholarship
              </button>

              <button
                onClick={() =>
                  setAiInput(
                    "How can I apply for a passport?"
                  )
                }
              >
                🛂 Passport
              </button>

              <button
                onClick={() =>
                  setAiInput(
                    "How can I apply for a government pension?"
                  )
                }
              >
                👵 Pension
              </button>
            </div>

            <div className="ai-chat-input">
              <textarea
                placeholder="Ask GovNavigator anything..."
                value={aiInput}
                onChange={(event) =>
                  setAiInput(event.target.value)
                }
                onKeyDown={handleAIKeyDown}
                rows="1"
              />

              <button
                onClick={sendAIMessage}
                disabled={
                  aiLoading ||
                  !aiInput.trim()
                }
              >
                ➤
              </button>
            </div>

            <p className="ai-disclaimer">
              GovNavigator AI provides general guidance.
              Always verify important information with
              the relevant official government authority.
            </p>
          </div>
        </div>
      )}

      {/* ============================================================
          LOGIN / REGISTER MODAL
          ============================================================ */}

      {showAuth && (
        <div
          onClick={closeAuth}
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 10000,
            background: "rgba(15, 23, 42, 0.58)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "20px",
            boxSizing: "border-box",
          }}
        >
          <div
            onClick={(event) => event.stopPropagation()}
            style={{
              width: "100%",
              maxWidth: "430px",
              background: "#ffffff",
              borderRadius: "22px",
              padding: "28px",
              boxShadow: "0 25px 80px rgba(15, 23, 42, 0.25)",
              boxSizing: "border-box",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
                gap: "15px",
                marginBottom: "20px",
              }}
            >
              <div>
                <p className="small-title" style={{ marginBottom: "6px" }}>
                  GOVNAVIGATOR ACCOUNT
                </p>

                <h2 style={{ margin: 0 }}>
                  {authMode === "login"
                    ? "Welcome back 👋"
                    : "Create your account 🚀"}
                </h2>

                <p
                  style={{
                    marginTop: "8px",
                    color: "#64748b",
                    lineHeight: 1.5,
                  }}
                >
                  {authMode === "login"
                    ? "Log in to use Smart Search and save your searches."
                    : "Create an account to personalize your GovNavigator experience."}
                </p>
              </div>

              <button
                type="button"
                onClick={closeAuth}
                disabled={authLoading}
                aria-label="Close authentication dialog"
                style={{
                  border: "none",
                  background: "#f1f5f9",
                  borderRadius: "10px",
                  width: "36px",
                  height: "36px",
                  cursor: "pointer",
                  fontSize: "18px",
                  flexShrink: 0,
                }}
              >
                ✕
              </button>
            </div>

            {authError && (
              <div
                style={{
                  background: "#fef2f2",
                  border: "1px solid #fecaca",
                  color: "#b91c1c",
                  borderRadius: "12px",
                  padding: "11px 13px",
                  marginBottom: "15px",
                  fontSize: "14px",
                  lineHeight: 1.45,
                }}
              >
                ⚠️ {authError}
              </div>
            )}

            {authSuccess && (
              <div
                style={{
                  background: "#f0fdf4",
                  border: "1px solid #bbf7d0",
                  color: "#166534",
                  borderRadius: "12px",
                  padding: "11px 13px",
                  marginBottom: "15px",
                  fontSize: "14px",
                  lineHeight: 1.45,
                }}
              >
                ✅ {authSuccess}
              </div>
            )}

            <form onSubmit={handleAuthSubmit}>
              {authMode === "register" && (
                <div style={{ marginBottom: "14px" }}>
                  <label
                    htmlFor="auth-name"
                    style={{
                      display: "block",
                      marginBottom: "7px",
                      fontWeight: 600,
                    }}
                  >
                    Full name
                  </label>

                  <input
                    id="auth-name"
                    type="text"
                    value={authName}
                    onChange={(event) => setAuthName(event.target.value)}
                    placeholder="Enter your name"
                    autoComplete="name"
                    disabled={authLoading}
                    style={{
                      width: "100%",
                      boxSizing: "border-box",
                      padding: "12px 13px",
                      border: "1px solid #cbd5e1",
                      borderRadius: "10px",
                      fontSize: "15px",
                    }}
                  />
                </div>
              )}

              <div style={{ marginBottom: "14px" }}>
                <label
                  htmlFor="auth-email"
                  style={{
                    display: "block",
                    marginBottom: "7px",
                    fontWeight: 600,
                  }}
                >
                  Email
                </label>

                <input
                  id="auth-email"
                  type="email"
                  value={authEmail}
                  onChange={(event) => setAuthEmail(event.target.value)}
                  placeholder="you@example.com"
                  autoComplete="email"
                  disabled={authLoading}
                  style={{
                    width: "100%",
                    boxSizing: "border-box",
                    padding: "12px 13px",
                    border: "1px solid #cbd5e1",
                    borderRadius: "10px",
                    fontSize: "15px",
                  }}
                />
              </div>

              <div style={{ marginBottom: "18px" }}>
                <label
                  htmlFor="auth-password"
                  style={{
                    display: "block",
                    marginBottom: "7px",
                    fontWeight: 600,
                  }}
                >
                  Password
                </label>

                <div style={{ position: "relative" }}>
                  <input
                    id="auth-password"
                    type={showAuthPassword ? "text" : "password"}
                    value={authPassword}
                    onChange={(event) => setAuthPassword(event.target.value)}
                    placeholder={
                      authMode === "register"
                        ? "Minimum 8 characters"
                        : "Enter your password"
                    }
                    autoComplete={
                      authMode === "register"
                        ? "new-password"
                        : "current-password"
                    }
                    disabled={authLoading}
                    style={{
                      width: "100%",
                      boxSizing: "border-box",
                      padding: "12px 48px 12px 13px",
                      border: "1px solid #cbd5e1",
                      borderRadius: "10px",
                      fontSize: "15px",
                    }}
                  />
                  <button
                    type="button"
                    aria-label={showAuthPassword ? "Hide password" : "Show password"}
                    title={showAuthPassword ? "Hide password" : "Show password"}
                    onClick={() => setShowAuthPassword((visible) => !visible)}
                    disabled={authLoading}
                    style={{
                      position: "absolute",
                      right: "8px",
                      top: "50%",
                      transform: "translateY(-50%)",
                      border: "none",
                      background: "transparent",
                      cursor: authLoading ? "not-allowed" : "pointer",
                      fontSize: "18px",
                      padding: "6px",
                    }}
                  >
                    {showAuthPassword ? "🙈" : "👁️"}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={authLoading}
                style={{
                  width: "100%",
                  border: "none",
                  background: "#0f172a",
                  color: "#ffffff",
                  borderRadius: "11px",
                  padding: "13px 16px",
                  cursor: authLoading ? "not-allowed" : "pointer",
                  fontWeight: 700,
                  fontSize: "15px",
                  opacity: authLoading ? 0.7 : 1,
                }}
              >
                {authLoading
                  ? "Please wait..."
                  : authMode === "login"
                    ? "Login"
                    : "Create Account"}
              </button>
            </form>

            <div
              style={{
                textAlign: "center",
                marginTop: "18px",
                color: "#64748b",
                fontSize: "14px",
              }}
            >
              {authMode === "login"
                ? "Don't have an account?"
                : "Already have an account?"}

              <button
                type="button"
                onClick={() => {
                  setAuthMode(
                    authMode === "login" ? "register" : "login"
                  );
                  setAuthError("");
                  setAuthSuccess("");
                  setAuthPassword("");
                }}
                disabled={authLoading}
                style={{
                  border: "none",
                  background: "transparent",
                  color: "#2563eb",
                  fontWeight: 700,
                  cursor: "pointer",
                  marginLeft: "5px",
                  padding: 0,
                }}
              >
                {authMode === "login" ? "Register" : "Login"}
              </button>
            </div>

            <p
              style={{
                marginTop: "18px",
                marginBottom: 0,
                fontSize: "12px",
                color: "#94a3b8",
                textAlign: "center",
                lineHeight: 1.5,
              }}
            >
              Your account is used only to authenticate GovNavigator
              features. Never share your password.
            </p>
          </div>
        </div>
            )}

      {showFavorites && (
        <div
          onClick={() => setShowFavorites(false)}
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 9998,
            background: "rgba(15, 23, 42, 0.58)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "20px",
            boxSizing: "border-box",
          }}
        >
          <div
            onClick={(event) => event.stopPropagation()}
            style={{
              width: "100%",
              maxWidth: "760px",
              maxHeight: "85vh",
              overflowY: "auto",
              background: "#ffffff",
              borderRadius: "22px",
              padding: "28px",
              boxShadow: "0 25px 80px rgba(15, 23, 42, 0.25)",
              boxSizing: "border-box",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "22px",
              }}
            >
              <div>
                <p
                  className="small-title"
                  style={{ marginBottom: "6px" }}
                >
                  GOVNAVIGATOR
                </p>

                <h2 style={{ margin: 0 }}>
                  ⭐ Saved Services
                </h2>

                <p
                  style={{
                    marginTop: "7px",
                    color: "#64748b",
                  }}
                >
                  Your saved government services
                </p>
              </div>

              <button
                type="button"
                onClick={() => setShowFavorites(false)}
                style={{
                  border: "none",
                  background: "#f1f5f9",
                  borderRadius: "10px",
                  width: "36px",
                  height: "36px",
                  cursor: "pointer",
                  fontSize: "18px",
                }}
              >
                ✕
              </button>
            </div>

            {favoritesLoading ? (
              <div
                style={{
                  textAlign: "center",
                  padding: "40px 20px",
                  color: "#64748b",
                }}
              >
                Loading your saved services...
              </div>
            ) : favoritesError ? (
              <div
                style={{
                  padding: "14px 16px",
                  marginBottom: "16px",
                  borderRadius: "12px",
                  background: "#fff7ed",
                  border: "1px solid #fed7aa",
                  color: "#9a3412",
                }}
              >
                {favoritesError}
              </div>
            ) : favorites.length === 0 ? (
              <div
                style={{
                  textAlign: "center",
                  padding: "50px 20px",
                  color: "#64748b",
                }}
              >
                <div style={{ fontSize: "42px", marginBottom: "12px" }}>
                  ☆
                </div>

                <h3 style={{ color: "#0f172a", marginBottom: "8px" }}>
                  No saved services yet
                </h3>

                <p style={{ margin: 0 }}>
                  Click the ☆ button on any service to save it here.
                </p>
              </div>
            ) : (
              <div
                style={{
                  display: "grid",
                  gap: "12px",
                }}
              >
                {favorites.map((favorite) => {
                  const favoriteService =
  unifiedServices.find(
    (service) =>
      Number(getDatabaseServiceId(service)) ===
      getFavoriteServiceId(favorite)
  ) || {
    id: String(getFavoriteServiceId(favorite) ?? ""),
    name: favorite.name || "Government Service",
    icon: "🏛️",
    description:
      favorite.description || "Saved government service.",
    eligibility:
      favorite.eligibility || "Information unavailable.",
    documents: Array.isArray(favorite.documents)
      ? favorite.documents
      : [],
    steps: Array.isArray(favorite.steps)
      ? favorite.steps
      : [],
    fees:
      favorite.fees ||
      "Verify the current fee on the official government portal.",
    processingTime:
      favorite.processing_time ||
      "Varies by service and authority.",
    mistakes: [],
  };

                  return (
                    <div
                      key={favorite.favorite_id || favorite.id}
                      style={{
                        border: "1px solid #e2e8f0",
                        borderRadius: "16px",
                        padding: "18px",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        gap: "16px",
                        flexWrap: "wrap",
                      }}
                    >
                      <div style={{ flex: 1, minWidth: "220px" }}>
                        <div
                          style={{
                            fontSize: "22px",
                            marginBottom: "5px",
                          }}
                        >
                          {favoriteService.icon}
                        </div>

                        <h3
                          style={{
                            margin: "0 0 6px",
                            color: "#0f172a",
                          }}
                        >
                          {favorite.name || favoriteService.name}
                        </h3>

                        <p
                          style={{
                            margin: 0,
                            color: "#64748b",
                            lineHeight: 1.5,
                          }}
                        >
                          {favorite.description ||
                            favoriteService.description}
                        </p>
                      </div>

                      <div
                        style={{
                          display: "flex",
                          gap: "8px",
                          alignItems: "center",
                        }}
                      >
                        <button
                          type="button"
                          onClick={() => {
                            setSelectedService(favoriteService);
                            setSearchPerformed(true);
                            setMatchScore(100);
                            setShowGuide(true);
                            setShowFavorites(false);
                            setTimeout(() => {
                              document
                                .getElementById("service-guide")
                                ?.scrollIntoView({
                                  behavior: "smooth",
                                  block: "start",
                                });
                            }, 50);
                          }}
                          style={{
                            border: "none",
                            background: "#0f172a",
                            color: "#ffffff",
                            borderRadius: "10px",
                            padding: "9px 13px",
                            cursor: "pointer",
                            fontWeight: 700,
                          }}
                        >
                          View Guide →
                        </button>

                        <button
                          type="button"
                          onClick={async () => {
  const serviceId = getFavoriteServiceId(favorite);

  if (!serviceId) {
    setFavoritesError(
      "Unable to identify this saved service."
    );
    return;
  }

  try {
    setFavoriteLoadingId(serviceId);
    setFavoritesError("");

    await removeFavorite(serviceId);

    setFavorites((previous) =>
      previous.filter(
        (item) => getFavoriteServiceId(item) !== serviceId
      )
    );

    await loadFavorites();
  } catch (error) {
    console.error(
      "Failed to remove favorite:",
      error
    );

    setFavoritesError(
      error?.message ||
        "Unable to remove saved service."
    );
  } finally {
    setFavoriteLoadingId(null);
  }
}}
                          
                          title="Remove from saved services"
                          style={{
                            border: "1px solid #fecaca",
                            background: "#fff1f2",
                            color: "#be123c",
                            borderRadius: "10px",
                            padding: "9px 11px",
                            cursor: "pointer",
                            fontWeight: 700,
                          }}
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}

      {showSearchHistory && (
        <div
          onClick={() => setShowSearchHistory(false)}
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 9999,
            background: "rgba(15, 23, 42, 0.58)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "20px",
            boxSizing: "border-box",
          }}
        >
          <div
            onClick={(event) => event.stopPropagation()}
            style={{
              width: "100%",
              maxWidth: "700px",
              maxHeight: "85vh",
              overflowY: "auto",
              background: "#ffffff",
              borderRadius: "22px",
              padding: "28px",
              boxShadow: "0 25px 80px rgba(15, 23, 42, 0.25)",
              boxSizing: "border-box",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "22px",
              }}
            >
              <div>
                <p
                  className="small-title"
                  style={{ marginBottom: "6px" }}
                >
                  GOVNAVIGATOR
                </p>

                <h2 style={{ margin: 0 }}>
                  📜 Search History
                </h2>

                <p
                  style={{
                    marginTop: "7px",
                    color: "#64748b",
                  }}
                >
                  Your previous government-service searches
                </p>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                {searchHistory.length > 0 && (
                  <button
                    type="button"
                    onClick={handleClearSearchHistory}
                    disabled={historyLoading}
                    style={{
                      border: "1px solid #fecaca",
                      background: "#fff1f2",
                      color: "#be123c",
                      borderRadius: "10px",
                      padding: "9px 12px",
                      cursor: historyLoading ? "not-allowed" : "pointer",
                      fontWeight: 700,
                    }}
                  >
                    🗑️ Clear All
                  </button>
                )}

              <button
                type="button"
                onClick={() => setShowSearchHistory(false)}
                style={{
                  border: "none",
                  background: "#f1f5f9",
                  borderRadius: "10px",
                  width: "36px",
                  height: "36px",
                  cursor: "pointer",
                  fontSize: "18px",
                }}
              >
                ✕
              </button>
              </div>
            </div>

            {historyLoading ? (
              <div
                style={{
                  textAlign: "center",
                  padding: "40px 20px",
                  color: "#64748b",
                }}
              >
                Loading your search history...
              </div>
            ) : historyError ? (
              <div
                style={{
                  textAlign: "center",
                  padding: "30px 20px",
                }}
              >
                <p style={{ color: "#b91c1c" }}>
                  ⚠️ {historyError}
                </p>

                <button
                  type="button"
                  onClick={loadSearchHistory}
                  style={{
                    border: "none",
                    background: "#0f172a",
                    color: "#ffffff",
                    padding: "10px 16px",
                    borderRadius: "10px",
                    cursor: "pointer",
                    fontWeight: 600,
                  }}
                >
                  Try Again
                </button>
              </div>
            ) : searchHistory.length === 0 ? (
              <div
                style={{
                  textAlign: "center",
                  padding: "45px 20px",
                  background: "#f8fafc",
                  borderRadius: "16px",
                }}
              >
                <div style={{ fontSize: "40px" }}>
                  🔎
                </div>

                <h3>No searches yet</h3>

                <p style={{ color: "#64748b" }}>
                  Your Smart Search activity will appear here.
                </p>
              </div>
            ) : (
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "12px",
                }}
              >
                {searchHistory.map((item) => (
                  <div
                    key={item.id}
                    style={{
                      border: "1px solid #e2e8f0",
                      borderRadius: "15px",
                      padding: "16px",
                      background: "#ffffff",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        gap: "15px",
                        flexWrap: "wrap",
                      }}
                    >
                      <div style={{ flex: 1 }}>
                        <h3
                          style={{
                            margin: "0 0 8px",
                            fontSize: "16px",
                          }}
                        >
                          🔍 {item.search_query}
                        </h3>

                        <p
                          style={{
                            margin: "5px 0",
                            color: "#475569",
                          }}
                        >
                          🏛️{" "}
                          {item.matched_service ||
                            "No matching service"}
                        </p>

                        <p
                          style={{
                            margin: "5px 0",
                            color: "#475569",
                          }}
                        >
                          📍{" "}
                          {item.selected_state ||
                            "All states"}
                        </p>
                      </div>

                      <div
                        style={{
                          display: "flex",
                          flexDirection: "column",
                          alignItems: "flex-end",
                          gap: "8px",
                        }}
                      >
                        <span
                          style={{
                            background: "#dcfce7",
                            color: "#166534",
                            padding: "6px 10px",
                            borderRadius: "20px",
                            fontSize: "13px",
                            fontWeight: 700,
                          }}
                        >
                          🎯 {item.match_score ?? 0}% match
                        </span>

                        <span
                          style={{
                            color: "#94a3b8",
                            fontSize: "12px",
                          }}
                        >
                          {item.created_at
                            ? new Date(
                                item.created_at
                              ).toLocaleString()
                            : ""}
                        </span>

                        <button
                          type="button"
                          onClick={() => handleDeleteSearchHistory(item.id)}
                          disabled={historyLoading}
                          title="Delete this search"
                          aria-label={`Delete search: ${item.search_query}`}
                          style={{
                            border: "1px solid #fecaca",
                            background: "#fff1f2",
                            color: "#be123c",
                            borderRadius: "10px",
                            padding: "7px 9px",
                            cursor: historyLoading ? "not-allowed" : "pointer",
                            fontSize: "15px",
                            fontWeight: 700,
                          }}
                        >
                          🗑️
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;