import { createBrowserRouter, Navigate } from "react-router-dom";
import { App } from "./App";
import { WelcomePage } from "../pages/welcome/WelcomePage";
import { RegisterPage } from "../pages/register/RegisterPage";
import { LoginPage } from "../pages/login/LoginPage";
import { OnboardingPage } from "../pages/onboarding/OnboardingPage";
import { ResultsPage } from "../pages/results/ResultsPage";
import { OpportunityPage } from "../pages/opportunity/OpportunityPage";
import { ProfilePage } from "../pages/profile/ProfilePage";
import { ProfileEditPage } from "../pages/profile/ProfileEditPage";
import { ProfileStatisticsPage } from "../pages/profile/ProfileStatisticsPage";
import { HistoryPage } from "../pages/history/HistoryPage";
import { SettingsPage } from "../pages/settings/SettingsPage";
import { NotFoundPage } from "../pages/errors/NotFoundPage";
import { OfflinePage } from "../pages/errors/OfflinePage";
import { FavoritesPage } from "../pages/profile/FavoritesPage";
import { NotificationsPage } from "../pages/notifications/NotificationsPage";

export const router = createBrowserRouter([
  {
    element: <App />,
    children: [
      { path: "/", element: <WelcomePage /> },
      { path: "/register", element: <RegisterPage /> },
      { path: "/login", element: <LoginPage /> },
      { path: "/onboarding/:step", element: <OnboardingPage /> },
      { path: "/app", element: <ProfileStatisticsPage /> },
      { path: "/results", element: <ResultsPage /> },
      { path: "/opportunities", element: <Navigate to="/results" replace /> },
      { path: "/opportunity/:id", element: <OpportunityPage /> },
      { path: "/profile", element: <ProfilePage /> },
      { path: "/profile/edit", element: <ProfileEditPage /> },
      { path: "/profile/statistics", element: <Navigate to="/app" replace /> },
      { path: "/profile/favorites", element: <FavoritesPage /> },
      { path: "/profile/statistics/settings", element: <Navigate to="/app" replace /> },
      { path: "/history", element: <HistoryPage /> },
      { path: "/notifications", element: <NotificationsPage /> },
      { path: "/settings", element: <SettingsPage /> },
      { path: "/offline", element: <OfflinePage /> },
      { path: "/404", element: <NotFoundPage /> },
      { path: "*", element: <Navigate to="/404" replace /> },
    ],
  },
]);