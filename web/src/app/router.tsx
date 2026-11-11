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
import { StatisticsSettingsPage } from "../pages/profile/StatisticsSettingsPage";
import { HistoryPage } from "../pages/history/HistoryPage";
import { SettingsPage } from "../pages/settings/SettingsPage";
import { NotFoundPage } from "../pages/errors/NotFoundPage";
import { OfflinePage } from "../pages/errors/OfflinePage";

export const router = createBrowserRouter([
  {
    element: <App />,
    children: [
      { path: "/", element: <WelcomePage /> },
      { path: "/register", element: <RegisterPage /> },
      { path: "/login", element: <LoginPage /> },
      { path: "/onboarding/:step", element: <OnboardingPage /> },
      { path: "/results", element: <ResultsPage /> },
      { path: "/opportunity/:id", element: <OpportunityPage /> },
      { path: "/profile", element: <ProfilePage /> },
      { path: "/profile/edit", element: <ProfileEditPage /> },
      { path: "/profile/statistics", element: <ProfileStatisticsPage /> },
      { path: "/profile/statistics/settings", element: <StatisticsSettingsPage /> },
      { path: "/history", element: <HistoryPage /> },
      { path: "/settings", element: <SettingsPage /> },
      { path: "/offline", element: <OfflinePage /> },
      { path: "/404", element: <NotFoundPage /> },
      { path: "*", element: <Navigate to="/404" replace /> },
    ],
  },
]);