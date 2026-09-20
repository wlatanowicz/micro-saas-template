import { translateApiError } from "@micro-saas/i18n";
import type { MeUser } from "@micro-saas/api-client";
import { useState } from "react";
import { Text, View } from "react-native";
import { useTranslation } from "react-i18next";

import { api } from "../api";
import { AppButton, Field } from "../ui";
import { useAppTheme } from "../theme";
import { SixCharCodeInput } from "./SixCharCodeInput";

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
  const theme = useAppTheme();
  const [active, setActive] = useState(0);
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");

  const sendCode = async () => {
    onError(null);
    onBusyChange(true);
    try {
      const result = await api.recoverySendCode(email);
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

  const handleVerifyNext = async () => {
    onError(null);
    onBusyChange(true);
    try {
      const result = await api.recoveryVerifyCode(email, code);
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
      const result = await api.recoveryComplete(email, code, password, passwordConfirm);
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
    <View style={{ gap: 12 }}>
      <StepHeader
        labels={[t("auth.steps.email"), t("auth.steps.code"), t("auth.steps.password")]}
        active={active}
      />
      {active === 0 ? (
        <View style={{ gap: 8 }}>
          <Field
            label={t("auth.email")}
            autoCapitalize="none"
            keyboardType="email-address"
            autoComplete="email"
            value={email}
            onChangeText={setEmail}
            editable={!busy}
          />
          <AppButton
            label={t("auth.sendRecoveryCode")}
            onPress={() => void handleEmailNext()}
            loading={busy}
          />
          <AppButton
            label={t("auth.backToSignIn")}
            variant="subtle"
            onPress={onBackToSignIn}
            disabled={busy}
          />
        </View>
      ) : null}
      {active === 1 ? (
        <View style={{ gap: 8 }}>
          <Text style={{ color: theme.dimmed }}>
            {t("auth.recovery.codeSent", { email: email || t("auth.recovery.thisEmail") })}
          </Text>
          <SixCharCodeInput
            label={t("auth.recoveryCode")}
            value={code}
            onChange={setCode}
            disabled={busy}
          />
          <AppButton label={t("auth.verifyCode")} onPress={() => void handleVerifyNext()} loading={busy} />
          <AppButton
            label={t("auth.resendCode")}
            variant="default"
            onPress={() => void sendCode()}
            loading={busy}
          />
        </View>
      ) : null}
      {active === 2 ? (
        <View style={{ gap: 8 }}>
          <Field
            label={t("auth.newPassword")}
            autoComplete="password-new"
            secureTextEntry
            value={password}
            onChangeText={setPassword}
            editable={!busy}
          />
          <Field
            label={t("auth.confirmNewPassword")}
            autoComplete="password-new"
            secureTextEntry
            value={passwordConfirm}
            onChangeText={setPasswordConfirm}
            editable={!busy}
          />
          <AppButton label={t("auth.resetPassword")} onPress={() => void handleComplete()} loading={busy} />
        </View>
      ) : null}
    </View>
  );
}

function StepHeader({ labels, active }: { labels: string[]; active: number }) {
  const theme = useAppTheme();
  return (
    <View style={{ flexDirection: "row", gap: 8 }}>
      {labels.map((label, index) => (
        <Text
          key={label}
          style={{
            color: index === active ? theme.text : theme.dimmed,
            fontWeight: index === active ? "700" : "400",
            fontSize: 13,
          }}
        >
          {index + 1}. {label}
        </Text>
      ))}
    </View>
  );
}
