import { Anchor, Button, Group, PasswordInput, Stack, TextInput } from "@mantine/core";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { translateApiError } from "../i18n/translateApiError";
import { signInRequest } from "./api";
import type { AuthConfig, MeUser } from "./types";

type SignInFormProps = {
  authConfig: AuthConfig;
  busy: boolean;
  onBusyChange: (busy: boolean) => void;
  onError: (message: string | null) => void;
  onSuccess: (user: MeUser, token: string) => void;
  onCreateAccount: () => void;
  onForgotPassword: () => void;
};

export function SignInForm({
  authConfig,
  busy,
  onBusyChange,
  onError,
  onSuccess,
  onCreateAccount,
  onForgotPassword,
}: SignInFormProps) {
  const { t } = useTranslation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSignIn = async () => {
    onError(null);
    onBusyChange(true);
    try {
      const result = await signInRequest(email, password);
      if (!result.ok) {
        onError(translateApiError(t, result.errorCode, result.errorParams));
        return;
      }
      onSuccess(result.data.user, result.data.access_token);
    } catch (e) {
      onError(e instanceof Error ? e.message : t("errors.requestFailed"));
    } finally {
      onBusyChange(false);
    }
  };

  return (
    <Stack gap="sm">
      <TextInput
        label={t("auth.email")}
        type="email"
        name="email"
        autoComplete="email"
        value={email}
        onChange={(e) => {
          setEmail(e.target.value);
        }}
        required
        disabled={busy}
      />
      <PasswordInput
        label={t("auth.password")}
        name="password"
        autoComplete="current-password"
        value={password}
        onChange={(e) => {
          setPassword(e.target.value);
        }}
        required
        disabled={busy}
      />
      <Group gap="sm">
        <Button type="button" onClick={() => void handleSignIn()} loading={busy}>
          {t("auth.signIn")}
        </Button>
      </Group>
      <Group gap="md">
        <Anchor component="button" type="button" size="sm" onClick={onCreateAccount}>
          {t("auth.createAccount")}
        </Anchor>
        {authConfig.password ? (
          <Anchor component="button" type="button" size="sm" onClick={onForgotPassword}>
            {t("auth.forgotPassword")}
          </Anchor>
        ) : null}
      </Group>
    </Stack>
  );
}
