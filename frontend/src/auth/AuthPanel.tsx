import { Alert, Button, Divider, Paper, Stack, Title } from "@mantine/core";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { apiBase } from "./api";
import { PasswordRecoveryWizard } from "./PasswordRecoveryWizard";
import { SignInForm } from "./SignInForm";
import { SignUpWizard } from "./SignUpWizard";
import type { AuthConfig, AuthView, MeUser } from "./types";

const ACCESS_TOKEN_KEY = "access_token";

type AuthPanelProps = {
  authConfig: AuthConfig;
  onSession: (user: MeUser, token: string) => void;
  initialError?: string | null;
};

export function AuthPanel({ authConfig, onSession, initialError = null }: AuthPanelProps) {
  const { t } = useTranslation();
  const [view, setView] = useState<AuthView>("signin");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(initialError);

  const methods: AuthConfig = authConfig;

  const handleSuccess = (user: MeUser, token: string) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, token);
    onSession(user, token);
  };

  const title =
    view === "signup"
      ? t("auth.createAccount")
      : view === "recovery"
        ? t("auth.resetPassword")
        : t("auth.signIn");

  return (
    <Paper withBorder p="md" radius="md" mb="md">
      <Title order={3} size="h4" mb="sm">
        {title}
      </Title>
      <Stack gap="md">
        {error ? (
          <Alert color="red" role="alert">
            {error}
          </Alert>
        ) : null}
        {view === "signin" && (methods.google || methods.facebook) ? (
          <Stack gap="xs">
            {methods.google ? (
              <Button
                component="a"
                href={`${apiBase()}/api/auth/google`}
                variant="default"
                fullWidth
              >
                {t("auth.continueWithGoogle")}
              </Button>
            ) : null}
            {methods.facebook ? (
              <Button
                component="a"
                href={`${apiBase()}/api/auth/facebook`}
                variant="default"
                fullWidth
              >
                {t("auth.continueWithFacebook")}
              </Button>
            ) : null}
          </Stack>
        ) : null}
        {view === "signin" && methods.password && (methods.google || methods.facebook) ? (
          <Divider label={t("auth.or")} labelPosition="center" />
        ) : null}
        {view === "signin" && methods.password ? (
          <SignInForm
            authConfig={methods}
            busy={busy}
            onBusyChange={setBusy}
            onError={setError}
            onSuccess={handleSuccess}
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
        {view === "signup" && methods.password ? (
          <SignUpWizard
            busy={busy}
            onBusyChange={setBusy}
            onError={setError}
            onSuccess={handleSuccess}
            onBackToSignIn={() => {
              setError(null);
              setView("signin");
            }}
          />
        ) : null}
        {view === "recovery" && methods.password ? (
          <PasswordRecoveryWizard
            busy={busy}
            onBusyChange={setBusy}
            onError={setError}
            onSuccess={handleSuccess}
            onBackToSignIn={() => {
              setError(null);
              setView("signin");
            }}
          />
        ) : null}
      </Stack>
    </Paper>
  );
}
