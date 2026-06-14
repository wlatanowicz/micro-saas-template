import { Button, Group, PasswordInput, Stack, Stepper, Text, TextInput } from "@mantine/core";
import { useState } from "react";

import { registerComplete, registerSendCode, registerVerifyCode } from "./api";
import { SixCharCodeInput } from "./SixCharCodeInput";
import type { MeUser } from "./types";

type SignUpWizardProps = {
  busy: boolean;
  onBusyChange: (busy: boolean) => void;
  onError: (message: string | null) => void;
  onSuccess: (user: MeUser, token: string) => void;
  onBackToSignIn: () => void;
};

export function SignUpWizard({
  busy,
  onBusyChange,
  onError,
  onSuccess,
  onBackToSignIn,
}: SignUpWizardProps) {
  const [active, setActive] = useState(0);
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");

  const sendCode = async () => {
    onError(null);
    onBusyChange(true);
    try {
      const result = await registerSendCode(email);
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
      const result = await registerVerifyCode(email, code);
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
      const result = await registerComplete(email, code, password, passwordConfirm);
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
        <Stepper.Step label="Email" description="Enter your email">
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
                Send code
              </Button>
              <Button type="button" variant="subtle" onClick={onBackToSignIn} disabled={busy}>
                Back to sign in
              </Button>
            </Group>
          </Stack>
        </Stepper.Step>
        <Stepper.Step label="Code" description="Enter verification code">
          <Stack gap="sm" mt="md">
            <Text size="sm" c="dimmed">
              We sent a 6-character code to {email || "your email"}.
            </Text>
            <SixCharCodeInput
              label="Verification code"
              value={code}
              onChange={setCode}
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
        <Stepper.Step label="Password" description="Set your password">
          <Stack gap="sm" mt="md">
            <PasswordInput
              label="Password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
              }}
              required
              disabled={busy}
            />
            <PasswordInput
              label="Confirm password"
              autoComplete="new-password"
              value={passwordConfirm}
              onChange={(e) => {
                setPasswordConfirm(e.target.value);
              }}
              required
              disabled={busy}
            />
            <Button type="button" onClick={() => void handleComplete()} loading={busy}>
              Create account
            </Button>
          </Stack>
        </Stepper.Step>
      </Stepper>
    </Stack>
  );
}
