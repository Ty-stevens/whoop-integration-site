import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";

import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorState } from "../components/ui/ErrorState";
import { LoadingState } from "../components/ui/LoadingState";
import { PageHeader } from "../components/ui/PageHeader";
import { SectionShell } from "../components/ui/SectionShell";
import { StatBlock } from "../components/ui/StatBlock";
import {
  apiFetch,
  type ActiveGoalProfileResponse,
  type AiBenchmarkUpdateResponse,
  type AiGoalSuggestionsResponse,
  type GoalProfile,
  type GoalProfileCreateInput,
  type GoalProfileListResponse
} from "../lib/api";
import { formatLongDate, getNextMondayDate } from "../lib/dates";
import { minutesLabel } from "../lib/format";

type GoalFormState = {
  effective_from_date: string;
  zone1_target_minutes: string;
  zone2_target_minutes: string;
  zone3_target_minutes: string;
  zone4_target_minutes: string;
  zone5_target_minutes: string;
  cardio_sessions_target: string;
  strength_sessions_target: string;
};

const emptyForm: GoalFormState = {
  effective_from_date: getNextMondayDate(),
  zone1_target_minutes: "0",
  zone2_target_minutes: "150",
  zone3_target_minutes: "0",
  zone4_target_minutes: "0",
  zone5_target_minutes: "0",
  cardio_sessions_target: "3",
  strength_sessions_target: "2"
};

function profileToForm(profile: GoalProfile): GoalFormState {
  return {
    effective_from_date: profile.effective_from_date,
    zone1_target_minutes: String(profile.zone1_target_minutes),
    zone2_target_minutes: String(profile.zone2_target_minutes),
    zone3_target_minutes: String(profile.zone3_target_minutes),
    zone4_target_minutes: String(profile.zone4_target_minutes),
    zone5_target_minutes: String(profile.zone5_target_minutes),
    cardio_sessions_target: String(profile.cardio_sessions_target),
    strength_sessions_target: String(profile.strength_sessions_target)
  };
}

function toNumber(value: string) {
  return Number(value || 0);
}

function formatGoalSummary(profile: GoalProfile) {
  return [
    `Z1 ${profile.zone1_target_minutes}`,
    `Z2 ${profile.zone2_target_minutes}`,
    `Z3 ${profile.zone3_target_minutes}`,
    `Z4 ${profile.zone4_target_minutes}`,
    `Z5 ${profile.zone5_target_minutes}`
  ].join(" · ");
}

export function GoalsPage() {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<GoalFormState>(emptyForm);

  const activeQuery = useQuery({
    queryKey: ["goals", "active"],
    queryFn: () => apiFetch<ActiveGoalProfileResponse>("/api/v1/goals/active")
  });

  const historyQuery = useQuery({
    queryKey: ["goals", "history"],
    queryFn: () => apiFetch<GoalProfileListResponse>("/api/v1/goals/history")
  });

  const createGoal = useMutation({
    mutationFn: (payload: GoalProfileCreateInput) =>
      apiFetch<GoalProfile>("/api/v1/goals/", {
        method: "POST",
        body: JSON.stringify(payload)
      }),
    onSuccess: async (data) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["goals", "active"] }),
        queryClient.invalidateQueries({ queryKey: ["goals", "history"] })
      ]);
      setForm(profileToForm(data));
    }
  });

  const goalSuggestions = useMutation({
    mutationFn: () =>
      apiFetch<AiGoalSuggestionsResponse>("/api/v1/ai/goal-suggestions", {
        method: "POST"
      })
  });

  const benchmarkUpdate = useMutation({
    mutationFn: (apply: boolean) =>
      apiFetch<AiBenchmarkUpdateResponse>("/api/v1/ai/benchmark-update", {
        method: "POST",
        body: JSON.stringify({
          apply,
          effective_from_date: form.effective_from_date
        })
      }),
    onSuccess: async (data) => {
      if (!data.applied || !data.profile) {
        return;
      }
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["goals", "active"] }),
        queryClient.invalidateQueries({ queryKey: ["goals", "history"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard", "current-week"] })
      ]);
      setForm(profileToForm(data.profile));
    }
  });

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    createGoal.mutate({
      effective_from_date: form.effective_from_date,
      zone1_target_minutes: toNumber(form.zone1_target_minutes),
      zone2_target_minutes: toNumber(form.zone2_target_minutes),
      zone3_target_minutes: toNumber(form.zone3_target_minutes),
      zone4_target_minutes: toNumber(form.zone4_target_minutes),
      zone5_target_minutes: toNumber(form.zone5_target_minutes),
      cardio_sessions_target: toNumber(form.cardio_sessions_target),
      strength_sessions_target: toNumber(form.strength_sessions_target)
    });
  }

  function loadBenchmarkTargets() {
    const targets = benchmarkUpdate.data?.proposal?.targets;
    if (!targets) {
      return;
    }
    setForm({
      effective_from_date: form.effective_from_date,
      zone1_target_minutes: String(targets.zone1_target_minutes),
      zone2_target_minutes: String(targets.zone2_target_minutes),
      zone3_target_minutes: String(targets.zone3_target_minutes),
      zone4_target_minutes: String(targets.zone4_target_minutes),
      zone5_target_minutes: String(targets.zone5_target_minutes),
      cardio_sessions_target: String(targets.cardio_sessions_target),
      strength_sessions_target: String(targets.strength_sessions_target)
    });
  }

  return (
    <>
      <PageHeader title="Goals" eyebrow="Weekly Targets" />

      {activeQuery.isLoading ? <LoadingState message="Loading active goal profile" /> : null}
      {historyQuery.isLoading ? <LoadingState message="Loading goal history" /> : null}
      {activeQuery.isError ? <ErrorState message="Active goal profile is unavailable." /> : null}
      {historyQuery.isError ? <ErrorState message="Goal history is unavailable." /> : null}

      <SectionShell title="Create Goal Profile">
        <Card>
          <form className="grid gap-4 lg:grid-cols-2" onSubmit={onSubmit}>
            <label className="grid gap-2 text-sm">
              Effective date
              <input
                className="rounded-md border border-line bg-raised px-3 py-2 text-primary"
                type="date"
                value={form.effective_from_date}
                onChange={(event) => setForm({ ...form, effective_from_date: event.target.value })}
              />
            </label>
            <div className="hidden lg:block" />
            <label className="grid gap-2 text-sm">
              Zone 1 target minutes
              <input
                className="rounded-md border border-line bg-raised px-3 py-2 text-primary"
                type="number"
                min="0"
                value={form.zone1_target_minutes}
                onChange={(event) => setForm({ ...form, zone1_target_minutes: event.target.value })}
              />
            </label>
            <label className="grid gap-2 text-sm">
              Zone 2 target minutes
              <input
                className="rounded-md border border-line bg-raised px-3 py-2 text-primary"
                type="number"
                min="0"
                value={form.zone2_target_minutes}
                onChange={(event) => setForm({ ...form, zone2_target_minutes: event.target.value })}
              />
            </label>
            <label className="grid gap-2 text-sm">
              Zone 3 target minutes
              <input
                className="rounded-md border border-line bg-raised px-3 py-2 text-primary"
                type="number"
                min="0"
                value={form.zone3_target_minutes}
                onChange={(event) => setForm({ ...form, zone3_target_minutes: event.target.value })}
              />
            </label>
            <label className="grid gap-2 text-sm">
              Zone 4 target minutes
              <input
                className="rounded-md border border-line bg-raised px-3 py-2 text-primary"
                type="number"
                min="0"
                value={form.zone4_target_minutes}
                onChange={(event) => setForm({ ...form, zone4_target_minutes: event.target.value })}
              />
            </label>
            <label className="grid gap-2 text-sm">
              Zone 5 target minutes
              <input
                className="rounded-md border border-line bg-raised px-3 py-2 text-primary"
                type="number"
                min="0"
                value={form.zone5_target_minutes}
                onChange={(event) => setForm({ ...form, zone5_target_minutes: event.target.value })}
              />
            </label>
            <label className="grid gap-2 text-sm">
              Cardio sessions
              <input
                className="rounded-md border border-line bg-raised px-3 py-2 text-primary"
                type="number"
                min="0"
                value={form.cardio_sessions_target}
                onChange={(event) => setForm({ ...form, cardio_sessions_target: event.target.value })}
              />
            </label>
            <label className="grid gap-2 text-sm">
              Strength sessions
              <input
                className="rounded-md border border-line bg-raised px-3 py-2 text-primary"
                type="number"
                min="0"
                value={form.strength_sessions_target}
                onChange={(event) => setForm({ ...form, strength_sessions_target: event.target.value })}
              />
            </label>
            <div className="lg:col-span-2 flex flex-wrap items-center gap-3">
              <Button type="submit" disabled={createGoal.isPending}>
                {createGoal.isPending ? "Saving" : "Save goal profile"}
              </Button>
              <p className="text-sm text-muted">The new profile becomes effective on the selected Monday.</p>
            </div>
            {createGoal.isError ? (
              <p className="lg:col-span-2 text-sm text-red-200">Could not save the goal profile. Check the values and retry.</p>
            ) : null}
          </form>
        </Card>
      </SectionShell>

      <SectionShell title="Active Goal">
        <div className="grid gap-4 lg:grid-cols-3">
          <Card className="lg:col-span-1">
            {activeQuery.data?.profile ? (
              <StatBlock
                label="Effective week"
                value={formatLongDate(activeQuery.data.profile.effective_from_date)}
                hint={activeQuery.data.message}
              />
            ) : (
              <div>
                <p className="font-semibold">No active profile</p>
                <p className="mt-2 text-sm text-muted">{activeQuery.data?.message ?? "Waiting for backend data."}</p>
              </div>
            )}
          </Card>
          {activeQuery.data?.profile ? (
            <Card className="lg:col-span-2">
              <div className="grid gap-3 sm:grid-cols-2">
                <StatBlock
                  label="Zone 2 target"
                  value={minutesLabel(activeQuery.data.profile.zone2_target_minutes)}
                  hint={formatGoalSummary(activeQuery.data.profile)}
                />
                <StatBlock
                  label="Cardio / strength"
                  value={`${activeQuery.data.profile.cardio_sessions_target} / ${activeQuery.data.profile.strength_sessions_target}`}
                  hint="Sessions per week"
                />
              </div>
            </Card>
          ) : (
            <EmptyState
              title="No active goal profile"
              body="Create a profile above to set the targets that Dashboard will use for the current week."
            />
          )}
        </div>
      </SectionShell>

      <SectionShell title="Advisory Goal Suggestions">
        <Card>
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <p className="font-semibold">Draft targets only</p>
              <p className="mt-1 text-sm text-muted">
                Suggestions never change goals until you review and save them through the normal form.
              </p>
              {goalSuggestions.data ? (
                <p className="mt-3 text-sm text-muted">{goalSuggestions.data.message}</p>
              ) : null}
            </div>
            <Button disabled={goalSuggestions.isPending} onClick={() => goalSuggestions.mutate()}>
              {goalSuggestions.isPending ? "Checking" : "Request suggestions"}
            </Button>
          </div>
          {goalSuggestions.data?.suggestions.length ? (
            <div className="mt-4 space-y-3">
              {goalSuggestions.data.suggestions.map((suggestion, index) => (
                <div key={index} className="rounded-md border border-line bg-raised p-4">
                  <p className="font-semibold">
                    Z2 {suggestion.zone2_target_minutes} min · cardio {suggestion.cardio_sessions_target} · strength {suggestion.strength_sessions_target}
                  </p>
                  <p className="mt-1 text-sm text-muted">{suggestion.rationale}</p>
                  <Button
                    className="mt-3"
                    variant="secondary"
                    onClick={() =>
                      setForm({
                        effective_from_date: form.effective_from_date,
                        zone1_target_minutes: String(suggestion.zone1_target_minutes),
                        zone2_target_minutes: String(suggestion.zone2_target_minutes),
                        zone3_target_minutes: String(suggestion.zone3_target_minutes),
                        zone4_target_minutes: String(suggestion.zone4_target_minutes),
                        zone5_target_minutes: String(suggestion.zone5_target_minutes),
                        cardio_sessions_target: String(suggestion.cardio_sessions_target),
                        strength_sessions_target: String(suggestion.strength_sessions_target)
                      })
                    }
                  >
                    Load into form
                  </Button>
                </div>
              ))}
            </div>
          ) : null}
          {goalSuggestions.isError ? (
            <p className="mt-3 text-sm text-red-200">Goal suggestions are unavailable.</p>
          ) : null}
        </Card>
      </SectionShell>

      <SectionShell title="AI Benchmark Update">
        <Card>
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <p className="font-semibold">Benchmark targets</p>
              <p className="mt-1 text-sm text-muted">
                Uses server-side report and WHOOP-derived metrics, then saves only after you apply.
              </p>
              {benchmarkUpdate.data ? (
                <p className="mt-3 text-sm text-muted">{benchmarkUpdate.data.message}</p>
              ) : null}
            </div>
            <div className="flex flex-wrap gap-2">
              <Button
                variant="secondary"
                disabled={benchmarkUpdate.isPending}
                onClick={() => benchmarkUpdate.mutate(false)}
              >
                {benchmarkUpdate.isPending ? "Checking" : "Preview update"}
              </Button>
              <Button
                disabled={benchmarkUpdate.isPending}
                onClick={() => benchmarkUpdate.mutate(true)}
              >
                {benchmarkUpdate.isPending ? "Applying" : "Apply AI update"}
              </Button>
            </div>
          </div>
          {benchmarkUpdate.data?.proposal ? (
            <div className="mt-4 space-y-3">
              <div className="rounded-md border border-line bg-raised p-4">
                <p className="font-semibold">
                  Z2 {benchmarkUpdate.data.proposal.targets.zone2_target_minutes} min · cardio{" "}
                  {benchmarkUpdate.data.proposal.targets.cardio_sessions_target} · strength{" "}
                  {benchmarkUpdate.data.proposal.targets.strength_sessions_target}
                </p>
                <p className="mt-1 text-sm text-muted">{benchmarkUpdate.data.proposal.summary}</p>
                <p className="mt-2 text-xs uppercase text-muted">
                  Confidence {benchmarkUpdate.data.proposal.confidence}
                </p>
                {!benchmarkUpdate.data.applied ? (
                  <Button className="mt-3" variant="secondary" onClick={loadBenchmarkTargets}>
                    Load into form
                  </Button>
                ) : null}
              </div>
              {benchmarkUpdate.data.proposal.changes.map((change) => (
                <div key={change.metric} className="rounded-md border border-line bg-surface p-4">
                  <p className="font-semibold">
                    {change.metric.split("_").join(" ")}: {change.current_value} to {change.recommended_value}
                  </p>
                  <p className="mt-1 text-sm text-muted">{change.reason}</p>
                  {change.sources.length ? (
                    <p className="mt-2 text-xs text-muted">
                      Sources{" "}
                      {change.sources
                        .map(
                          (source) =>
                            `${source.source_type}${source.date ? ` ${source.date}` : ""} ${source.metric}`
                        )
                        .join(" · ")}
                    </p>
                  ) : null}
                </div>
              ))}
            </div>
          ) : null}
          {benchmarkUpdate.isError ? (
            <p className="mt-3 text-sm text-red-200">AI benchmark update is unavailable.</p>
          ) : null}
        </Card>
      </SectionShell>

      <SectionShell title="Goal History">
        <Card>
          {historyQuery.data?.profiles?.length ? (
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead className="text-muted">
                  <tr>
                    <th className="py-2 pr-4 font-medium">Effective date</th>
                    <th className="py-2 pr-4 font-medium">Zone 2</th>
                    <th className="py-2 pr-4 font-medium">Cardio</th>
                    <th className="py-2 pr-4 font-medium">Strength</th>
                    <th className="py-2 pr-4 font-medium">Created</th>
                  </tr>
                </thead>
                <tbody>
                  {historyQuery.data.profiles.map((profile) => {
                    const isActive = activeQuery.data?.profile?.id === profile.id;
                    return (
                      <tr key={profile.id} className={isActive ? "text-accent" : ""}>
                        <td className="py-2 pr-4">
                          <div className="font-semibold">
                            {formatLongDate(profile.effective_from_date)}
                            {isActive ? <span className="ml-2 text-xs uppercase text-muted">Current</span> : null}
                          </div>
                        </td>
                        <td className="py-2 pr-4">{minutesLabel(profile.zone2_target_minutes)}</td>
                        <td className="py-2 pr-4">{profile.cardio_sessions_target}</td>
                        <td className="py-2 pr-4">{profile.strength_sessions_target}</td>
                        <td className="py-2 pr-4">{new Date(profile.created_at_utc).toLocaleString()}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyState title="No goal history yet" body="Create the first profile above and it will appear here with the active row." />
          )}
        </Card>
      </SectionShell>
    </>
  );
}
