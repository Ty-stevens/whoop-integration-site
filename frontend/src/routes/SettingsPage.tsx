import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useEffect, useState } from "react";

import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorState } from "../components/ui/ErrorState";
import { LoadingState } from "../components/ui/LoadingState";
import { PageHeader } from "../components/ui/PageHeader";
import { SectionShell } from "../components/ui/SectionShell";
import { apiFetch, apiOpenRedirect, type AiStatus, type AppSettings, type AthleteProfile, type WhoopStatus } from "../lib/api";

type ProfileForm = {
  display_name: string;
  gender: string;
  age_years: string;
  height_cm: string;
  weight_kg: string;
  training_focus: string;
  experience_level: string;
  notes_for_ai: string;
};

const emptyProfileForm: ProfileForm = {
  display_name: "",
  gender: "",
  age_years: "",
  height_cm: "",
  weight_kg: "",
  training_focus: "",
  experience_level: "",
  notes_for_ai: ""
};

function profileToForm(profile: AthleteProfile): ProfileForm {
  return {
    display_name: profile.display_name ?? "",
    gender: profile.gender ?? "",
    age_years: profile.age_years?.toString() ?? "",
    height_cm: profile.height_cm?.toString() ?? "",
    weight_kg: profile.weight_kg?.toString() ?? "",
    training_focus: profile.training_focus ?? "",
    experience_level: profile.experience_level ?? "",
    notes_for_ai: profile.notes_for_ai ?? ""
  };
}

function nullableNumber(value: string) {
  return value.trim() ? Number(value) : null;
}

function nullableString(value: string) {
  return value.trim() ? value.trim() : null;
}

export function SettingsPage() {
  const queryClient = useQueryClient();
  const [profileForm, setProfileForm] = useState<ProfileForm>(emptyProfileForm);

  const whoopQuery = useQuery({
    queryKey: ["whoop-status"],
    queryFn: () => apiFetch<WhoopStatus>("/api/v1/integrations/whoop/status")
  });

  const settingsQuery = useQuery({
    queryKey: ["settings"],
    queryFn: () => apiFetch<AppSettings>("/api/v1/settings")
  });

  const profileQuery = useQuery({
    queryKey: ["athlete-profile"],
    queryFn: () => apiFetch<AthleteProfile>("/api/v1/athlete-profile")
  });

  const aiStatusQuery = useQuery({
    queryKey: ["ai-status"],
    queryFn: () => apiFetch<AiStatus>("/api/v1/ai/status")
  });

  useEffect(() => {
    if (profileQuery.data) {
      setProfileForm(profileToForm(profileQuery.data));
    }
  }, [profileQuery.data]);

  const saveProfile = useMutation({
    mutationFn: () =>
      apiFetch<AthleteProfile>("/api/v1/athlete-profile", {
        method: "PUT",
        body: JSON.stringify({
          display_name: nullableString(profileForm.display_name),
          gender: nullableString(profileForm.gender),
          age_years: nullableNumber(profileForm.age_years),
          height_cm: nullableNumber(profileForm.height_cm),
          weight_kg: nullableNumber(profileForm.weight_kg),
          training_focus: nullableString(profileForm.training_focus),
          experience_level: nullableString(profileForm.experience_level),
          notes_for_ai: nullableString(profileForm.notes_for_ai)
        })
      }),
    onSuccess: (data) => {
      queryClient.setQueryData(["athlete-profile"], data);
    }
  });

  const saveSettings = useMutation({
    mutationFn: (payload: AppSettings) =>
      apiFetch<AppSettings>("/api/v1/settings", {
        method: "PUT",
        body: JSON.stringify(payload)
      }),
    onSuccess: (data) => {
      queryClient.setQueryData(["settings"], data);
    }
  });

  const disconnectWhoop = useMutation({
    mutationFn: () =>
      apiFetch<{ status: string; message: string }>("/api/v1/integrations/whoop/disconnect", {
        method: "POST"
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["whoop-status"] });
    }
  });

  const connectWhoop = useMutation({
    mutationFn: async () => {
      await apiOpenRedirect("/api/v1/integrations/whoop/connect");
      return true;
    }
  });

  function onProfileSubmit(event: FormEvent) {
    event.preventDefault();
    saveProfile.mutate();
  }

  return (
    <>
      <PageHeader title="Settings" eyebrow="Private Control" />

      <SectionShell title="WHOOP Connection">
        <Card>
          {whoopQuery.isLoading ? <LoadingState message="Checking WHOOP connection" /> : null}
          {whoopQuery.isError ? <ErrorState message="WHOOP status is unavailable. Start the backend and retry." /> : null}
          {whoopQuery.data ? (
            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <p className="text-lg font-semibold">{whoopQuery.data.status.replace("_", " ")}</p>
                <p className="mt-1 text-sm text-muted">{whoopQuery.data.message}</p>
                {whoopQuery.data.connected_at_utc ? (
                  <p className="mt-2 text-xs text-muted">
                    Connected {new Date(whoopQuery.data.connected_at_utc).toLocaleString()}
                  </p>
                ) : null}
                {whoopQuery.data.token_expires_at_utc ? (
                  <p className="mt-1 text-xs text-muted">
                    Token expires {new Date(whoopQuery.data.token_expires_at_utc).toLocaleString()}
                  </p>
                ) : null}
                {whoopQuery.data.granted_scopes ? (
                  <p className="mt-1 text-xs text-muted">Scopes {whoopQuery.data.granted_scopes}</p>
                ) : null}
              </div>
              <div className="flex flex-wrap gap-2">
                <Button
                  disabled={connectWhoop.isPending}
                  onClick={() => connectWhoop.mutate()}
                >
                  {connectWhoop.isPending
                    ? "Opening WHOOP..."
                    : whoopQuery.data.status === "connected"
                      ? "Reconnect WHOOP"
                      : "Connect WHOOP"}
                </Button>
                {whoopQuery.data.status === "connected" || whoopQuery.data.status === "expired" ? (
                  <Button
                    variant="secondary"
                    disabled={disconnectWhoop.isPending}
                    onClick={() => disconnectWhoop.mutate()}
                  >
                    Disconnect
                  </Button>
                ) : null}
              </div>
            </div>
          ) : null}
        </Card>
      </SectionShell>

      <SectionShell title="Athlete Profile">
        <Card>
          {profileQuery.isLoading ? <LoadingState message="Loading profile" /> : null}
          {profileQuery.isError ? <ErrorState message="Athlete profile is unavailable." /> : null}
          <form className="grid gap-4 lg:grid-cols-2" onSubmit={onProfileSubmit}>
            <label className="grid gap-2 text-sm">
              Display name
              <input
                className="rounded-md border border-line bg-raised px-3 py-2 text-primary"
                value={profileForm.display_name}
                onChange={(event) => setProfileForm({ ...profileForm, display_name: event.target.value })}
              />
            </label>
            <label className="grid gap-2 text-sm">
              Gender
              <input
                className="rounded-md border border-line bg-raised px-3 py-2 text-primary"
                value={profileForm.gender}
                onChange={(event) => setProfileForm({ ...profileForm, gender: event.target.value })}
              />
            </label>
            <label className="grid gap-2 text-sm">
              Age
              <input
                className="rounded-md border border-line bg-raised px-3 py-2 text-primary"
                type="number"
                min="13"
                max="120"
                value={profileForm.age_years}
                onChange={(event) => setProfileForm({ ...profileForm, age_years: event.target.value })}
              />
            </label>
            <label className="grid gap-2 text-sm">
              Height cm
              <input
                className="rounded-md border border-line bg-raised px-3 py-2 text-primary"
                type="number"
                min="80"
                max="260"
                value={profileForm.height_cm}
                onChange={(event) => setProfileForm({ ...profileForm, height_cm: event.target.value })}
              />
            </label>
            <label className="grid gap-2 text-sm">
              Weight kg
              <input
                className="rounded-md border border-line bg-raised px-3 py-2 text-primary"
                type="number"
                min="25"
                max="350"
                value={profileForm.weight_kg}
                onChange={(event) => setProfileForm({ ...profileForm, weight_kg: event.target.value })}
              />
            </label>
            <label className="grid gap-2 text-sm">
              Experience
              <select
                className="rounded-md border border-line bg-raised px-3 py-2 text-primary"
                value={profileForm.experience_level}
                onChange={(event) => setProfileForm({ ...profileForm, experience_level: event.target.value })}
              >
                <option value="">Unset</option>
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
                <option value="elite">Elite</option>
              </select>
            </label>
            <label className="grid gap-2 text-sm lg:col-span-2">
              Training focus
              <textarea
                className="min-h-24 rounded-md border border-line bg-raised px-3 py-2 text-primary"
                value={profileForm.training_focus}
                onChange={(event) => setProfileForm({ ...profileForm, training_focus: event.target.value })}
              />
            </label>
            <label className="grid gap-2 text-sm lg:col-span-2">
              AI notes
              <textarea
                className="min-h-24 rounded-md border border-line bg-raised px-3 py-2 text-primary"
                value={profileForm.notes_for_ai}
                onChange={(event) => setProfileForm({ ...profileForm, notes_for_ai: event.target.value })}
              />
            </label>
            <div className="lg:col-span-2">
              <Button type="submit" disabled={saveProfile.isPending}>
                {saveProfile.isPending ? "Saving" : "Save profile"}
              </Button>
              {saveProfile.isError ? <p className="mt-2 text-sm text-red-200">Profile validation failed.</p> : null}
              {saveProfile.isSuccess ? <p className="mt-2 text-sm text-accent">Profile saved.</p> : null}
            </div>
          </form>
        </Card>
      </SectionShell>

      <SectionShell title="App Preferences">
        <Card>
          {settingsQuery.data ? (
            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <p className="font-semibold">Auto-sync</p>
                <p className="text-sm text-muted">
                  {settingsQuery.data.auto_sync_enabled ? "Enabled" : "Off"} · {settingsQuery.data.auto_sync_frequency}
                </p>
              </div>
              <Button
                variant="secondary"
                disabled={saveSettings.isPending}
                onClick={() =>
                  saveSettings.mutate({
                    ...settingsQuery.data,
                    auto_sync_enabled: !settingsQuery.data.auto_sync_enabled
                  })
                }
              >
                Toggle auto-sync
              </Button>
            </div>
          ) : (
            <EmptyState title="Preferences unavailable" body="Start the backend to edit local app preferences." />
          )}
        </Card>
      </SectionShell>

      <SectionShell title="AI Status">
        <Card>
          {aiStatusQuery.isLoading ? <LoadingState message="Checking AI status" /> : null}
          {aiStatusQuery.isError ? <ErrorState message="AI status is unavailable." /> : null}
          {aiStatusQuery.data ? (
            <div className="grid gap-3 text-sm sm:grid-cols-3">
              <div>
                <p className="text-muted">Status</p>
                <p className="font-semibold">{aiStatusQuery.data.status}</p>
              </div>
              <div>
                <p className="text-muted">Provider</p>
                <p className="font-semibold">{aiStatusQuery.data.provider}</p>
              </div>
              <div>
                <p className="text-muted">Model</p>
                <p className="font-semibold">{aiStatusQuery.data.model ?? "Unset"}</p>
              </div>
              <p className="sm:col-span-3 text-muted">{aiStatusQuery.data.message}</p>
            </div>
          ) : null}
        </Card>
      </SectionShell>
    </>
  );
}
