import { Anchor, Button, Group, PasswordInput, Stack, TextInput } from "@mantine/core";
import { useState } from "react";

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
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSignIn = async () => {
    onError(null);
    onBusyChange(true);
    try {
      const result = await signInRequest(email, password);
      if (!result.ok) {
        onError(result.error);
        return;
      }
      onSuccess(result.data.user, result.data.access_token);
    } catch (e) {
      onError(e instanceof Error ? e.message : "Request failed");
    } finally {
      onBusyChange(false);
    }
  };

  return (
    <Stack gap="sm">
      <TextInput
        label="Email"
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
        label="Password"
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
          Sign in
        </Button>
      </Group>
      <Group gap="md">
        <Anchor component="button" type="button" size="sm" onClick={onCreateAccount}>
          Create account
        </Anchor>
        {authConfig.password ? (
          <Anchor component="button" type="button" size="sm" onClick={onForgotPassword}>
            Forgot password?
          </Anchor>
        ) : null}
      </Group>
    </Stack>
  );
}
