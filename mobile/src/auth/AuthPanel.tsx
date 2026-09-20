import type { AuthConfig, AuthView, MeUser, OAuthProvider } from "@micro-saas/api-client";
import { translateApiError } from "@micro-saas/i18n";
import { useState } from "react";
import { Text, View } from "react-native";
import { useTranslation } from "react-i18next";

import { api } from "../api";
import { setAccessToken } from "../session";
import { AppButton, Card, ErrorBanner } from "../ui";
import { useAppTheme } from "../theme";
import { PasswordRecoveryWizard } from "./PasswordRecoveryWizard";
import { SignInForm } from "./SignInForm";
import { SignUpWizard } from "./SignUpWizard";
import { startOAuth } from "./oauth";

type AuthPanelProps = {
  authConfig: AuthConfig;
  onSession: (user: MeUser, token: string) => void;
  initialError?: string | null;
};

export function AuthPanel({ authConfig, onSession, initialError = null }: AuthPanelProps) {
  const { t } = useTranslation();
  const theme = useAppTheme();
  const [view, setView] = useState<AuthView>("signin");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(initialError);

  const handleSuccess = async (user: MeUser, token: string) => {
    await setAccessToken(token);
    onSession(user, token);
  };

  const handleOAuth = async (provider: OAuthProvider) => {
    setError(null);
    setBusy(true);
    try {
      const result = await startOAuth(provider);
      if (result.authErrorCode) {
        setError(translateApiError(t, result.authErrorCode));
        return;
      }
      if (!result.accessToken) {
        return;
      }
      const me = await api.loadMe(result.accessToken);
      if (!me.ok) {
        setError(translateApiError(t, me.errorCode, me.errorParams));
        return;
      }
      await handleSuccess(me.data, result.accessToken);
    } catch (e) {
      setError(e instanceof Error ? e.message : t("errors.requestFailed"));
    } finally {
      setBusy(false);
    }
  };

  const title =
    view === "signup"
      ? t("auth.createAccount")
      : view === "recovery"
        ? t("auth.resetPassword")
        : t("auth.signIn");

  return (
    <Card>
      <Text style={{ color: theme.text, fontSize: 18, fontWeight: "700", marginBottom: 12 }}>{title}</Text>
      <View style={{ gap: 12 }}>
        {error ? <ErrorBanner message={error} /> : null}
        {view === "signin" && (authConfig.google || authConfig.facebook) ? (
          <View style={{ gap: 8 }}>
            {authConfig.google ? (
              <AppButton
                label={t("auth.continueWithGoogle")}
                variant="default"
                disabled={busy}
                onPress={() => void handleOAuth("google")}
              />
            ) : null}
            {authConfig.facebook ? (
              <AppButton
                label={t("auth.continueWithFacebook")}
                variant="default"
                disabled={busy}
                onPress={() => void handleOAuth("facebook")}
              />
            ) : null}
          </View>
        ) : null}
        {view === "signin" && authConfig.password && (authConfig.google || authConfig.facebook) ? (
          <Text style={{ color: theme.dimmed, textAlign: "center" }}>{t("auth.or")}</Text>
        ) : null}
        {view === "signin" && authConfig.password ? (
          <SignInForm
            authConfig={authConfig}
            busy={busy}
            onBusyChange={setBusy}
            onError={setError}
            onSuccess={(user, token) => {
              void handleSuccess(user, token);
            }}
            onCreateAccount={() => {
              setError(null);
              setView("signup");
            }}
            onForgotPassword={() => {
              setError(null);
              setView("recovery");
            }}
          />
        ) : null}
        {view === "signup" && authConfig.password ? (
          <SignUpWizard
            busy={busy}
            onBusyChange={setBusy}
            onError={setError}
            onSuccess={(user, token) => {
              void handleSuccess(user, token);
            }}
            onBackToSignIn={() => {
              setError(null);
              setView("signin");
            }}
          />
        ) : null}
        {view === "recovery" && authConfig.password ? (
          <PasswordRecoveryWizard
            busy={busy}
            onBusyChange={setBusy}
            onError={setError}
            onSuccess={(user, token) => {
              void handleSuccess(user, token);
            }}
            onBackToSignIn={() => {
              setError(null);
              setView("signin");
            }}
          />
        ) : null}
      </View>
    </Card>
  );
}
