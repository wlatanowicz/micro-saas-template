import { Button, Group, PasswordInput, Stack, Stepper, Text, TextInput } from "@mantine/core";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { translateApiError } from "../i18n/translateApiError";
import { recoveryComplete, recoverySendCode, recoveryVerifyCode } from "./api";
import { SixCharCodeInput } from "./SixCharCodeInput";
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
  const { t } = useTranslation();
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
        onError(translateApiError(t, result.errorCode, result.errorParams));
        return false;
      }
      return true;
    } catch (e) {
      onError(e instanceof Error ? e.message : t("errors.requestFailed"));
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
        onError(translateApiError(t, result.errorCode, result.errorParams));
        return;
      }
      setActive(2);
    } catch (e) {
      onError(e instanceof Error ? e.message : t("errors.requestFailed"));
    } finally {
      onBusyChange(false);
    }
  };

  const handleComplete = async () => {
    if (password !== passwordConfirm) {
      onError(translateApiError(t, "passwords_do_not_match"));
      return;
    }
    onError(null);
    onBusyChange(true);
    try {
      const result = await recoveryComplete(email, code, password, passwordConfirm);
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
    <Stack gap="md">
      <Stepper active={active} onStepClick={setActive} allowNextStepsSelect={false}>
        <Stepper.Step
          label={t("auth.steps.email")}
          description={t("auth.steps.confirmAccount")}
        >
          <Stack gap="sm" mt="md">
            <TextInput
              label={t("auth.email")}
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
                {t("auth.sendRecoveryCode")}
              </Button>
              <Button type="button" variant="subtle" onClick={onBackToSignIn} disabled={busy}>
                {t("auth.backToSignIn")}
              </Button>
            </Group>
          </Stack>
        </Stepper.Step>
        <Stepper.Step
          label={t("auth.steps.code")}
          description={t("auth.steps.enterRecoveryCode")}
        >
          <Stack gap="sm" mt="md">
            <Text size="sm" c="dimmed">
              {t("auth.recovery.codeSent", {
                email: email || t("auth.recovery.thisEmail"),
              })}
            </Text>
            <SixCharCodeInput
              label={t("auth.recoveryCode")}
              value={code}
              onChange={setCode}
              disabled={busy}
            />
            <Group gap="sm">
              <Button type="button" onClick={() => void handleVerifyNext()} loading={busy}>
                {t("auth.verifyCode")}
              </Button>
              <Button
                type="button"
                variant="default"
                onClick={() => void handleResendCode()}
                loading={busy}
              >
                {t("auth.resendCode")}
              </Button>
            </Group>
          </Stack>
        </Stepper.Step>
        <Stepper.Step
          label={t("auth.steps.password")}
          description={t("auth.steps.chooseNewPassword")}
        >
          <Stack gap="sm" mt="md">
            <PasswordInput
              label={t("auth.newPassword")}
              autoComplete="new-password"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
              }}
              required
              disabled={busy}
            />
            <PasswordInput
              label={t("auth.confirmNewPassword")}
              autoComplete="new-password"
              value={passwordConfirm}
              onChange={(e) => {
                setPasswordConfirm(e.target.value);
              }}
              required
              disabled={busy}
            />
            <Button type="button" onClick={() => void handleComplete()} loading={busy}>
              {t("auth.resetPassword")}
            </Button>
          </Stack>
        </Stepper.Step>
      </Stepper>
    </Stack>
  );
}
