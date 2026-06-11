import { Button, Group, PasswordInput, Stack, Stepper, Text, TextInput } from "@mantine/core";
import { useState } from "react";

import { recoveryComplete, recoverySendCode, recoveryVerifyCode } from "./api";
import type { MeUser } from "./types";

type PasswordRecoveryWizardProps = {
  busy: boolean;
  onBusyChange: (busy: boolean) => void;
  onError: (message: string | null) => void;
  onSuccess: (user: MeUser, token: string) => void;
  onBackToSignIn: () => void;
};

export function PasswordRecoveryWizard({
  busy,
  onBusyChange,
  onError,
  onSuccess,
  onBackToSignIn,
}: PasswordRecoveryWizardProps) {
  const [active, setActive] = useState(0);
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");

  const sendCode = async () => {
    onError(null);
    onBusyChange(true);
    try {
      const result = await recoverySendCode(email);
      if (!result.ok) {
        onError(result.error);
        return false;
      }
      return true;
    } catch (e) {
      onError(e instanceof Error ? e.message : "Request failed");
      return false;
    } finally {
      onBusyChange(false);
    }
  };

  const handleEmailNext = async () => {
    const ok = await sendCode();
    if (ok) {
      setActive(1);
    }
  };

  const handleResendCode = async () => {
    await sendCode();
  };

  const handleVerifyNext = async () => {
    onError(null);
    onBusyChange(true);
    try {
      const result = await recoveryVerifyCode(email, code);
      if (!result.ok) {
        onError(result.error);
        return;
      }
      setActive(2);
    } catch (e) {
      onError(e instanceof Error ? e.message : "Request failed");
    } finally {
      onBusyChange(false);
    }
  };

  const handleComplete = async () => {
    if (password !== passwordConfirm) {
      onError("Passwords do not match");
      return;
    }
    onError(null);
    onBusyChange(true);
    try {
      const result = await recoveryComplete(email, code, password, passwordConfirm);
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
    <Stack gap="md">
      <Stepper active={active} onStepClick={setActive} allowNextStepsSelect={false}>
        <Stepper.Step label="Email" description="Confirm your account">
          <Stack gap="sm" mt="md">
            <TextInput
              label="Email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
              }}
              required
              disabled={busy}
            />
            <Group gap="sm">
              <Button type="button" onClick={() => void handleEmailNext()} loading={busy}>
                Send recovery code
              </Button>
              <Button type="button" variant="subtle" onClick={onBackToSignIn} disabled={busy}>
                Back to sign in
              </Button>
            </Group>
          </Stack>
        </Stepper.Step>
        <Stepper.Step label="Code" description="Enter recovery code">
          <Stack gap="sm" mt="md">
            <Text size="sm" c="dimmed">
              If an account exists for {email || "this email"}, we sent a 6-character code.
            </Text>
            <TextInput
              label="Recovery code"
              value={code}
              onChange={(e) => {
                setCode(e.target.value.toUpperCase());
              }}
              maxLength={6}
              required
              disabled={busy}
            />
            <Group gap="sm">
              <Button type="button" onClick={() => void handleVerifyNext()} loading={busy}>
                Verify code
              </Button>
              <Button
                type="button"
                variant="default"
                onClick={() => void handleResendCode()}
                loading={busy}
              >
                Resend code
              </Button>
            </Group>
          </Stack>
        </Stepper.Step>
        <Stepper.Step label="Password" description="Choose a new password">
          <Stack gap="sm" mt="md">
            <PasswordInput
              label="New password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
              }}
              required
              disabled={busy}
            />
            <PasswordInput
              label="Confirm new password"
              autoComplete="new-password"
              value={passwordConfirm}
              onChange={(e) => {
                setPasswordConfirm(e.target.value);
              }}
              required
              disabled={busy}
            />
            <Button type="button" onClick={() => void handleComplete()} loading={busy}>
              Reset password
            </Button>
          </Stack>
        </Stepper.Step>
      </Stepper>
    </Stack>
  );
}
