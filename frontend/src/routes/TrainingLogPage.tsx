import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

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
  type Classification,
  type RecentWorkoutsResponse,
  type StrengthOverview,
  type StrengthSplit,
  type WorkoutAnnotation,
  type WorkoutAnnotationInput,
  type WorkoutSummary
} from "../lib/api";
import { formatLongDate } from "../lib/dates";
import { zoneColors, zoneLabels } from "../lib/zones";

type FormState = {
  manual_classification: "" | Classification;
  manual_strength_split: "" | StrengthSplit;
  tag: string;
  notes: string;
};

function secondsLabel(seconds: number) {
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) {
    return `${minutes} min`;
  }
  const hours = Math.floor(minutes / 60);
  const remainder = minutes % 60;
  return remainder ? `${hours} hr ${remainder} min` : `${hours} hr`;
}

function formFromAnnotation(annotation: WorkoutAnnotation | null): FormState {
  return {
    manual_classification: annotation?.manual_classification ?? "",
    manual_strength_split: annotation?.manual_strength_split ?? "",
    tag: annotation?.tag ?? "",
    notes: annotation?.notes ?? ""
  };
}

function nullable(value: string) {
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
}

function workoutZones(workout: WorkoutSummary) {
  return [1, 2, 3, 4, 5].map((zone) => ({
    zone,
    seconds: workout[`zone${zone}_seconds` as keyof Pick<
      WorkoutSummary,
      "zone1_seconds" | "zone2_seconds" | "zone3_seconds" | "zone4_seconds" | "zone5_seconds"
    >] as number
  }));
}

export function TrainingLogPage() {
  const queryClient = useQueryClient();
  const [forms, setForms] = useState<Record<number, FormState>>({});

  const workoutsQuery = useQuery({
    queryKey: ["workouts", "recent"],
    queryFn: () => apiFetch<RecentWorkoutsResponse>("/api/v1/workouts/recent?limit=50")
  });

  const strengthQuery = useQuery({
    queryKey: ["workouts", "strength-overview"],
    queryFn: () => apiFetch<StrengthOverview>("/api/v1/workouts/strength-overview?limit=180")
  });

  const saveAnnotation = useMutation({
    mutationFn: ({ workoutId, payload }: { workoutId: number; payload: WorkoutAnnotationInput }) =>
      apiFetch<WorkoutAnnotation>(`/api/v1/workouts/${workoutId}/annotation`, {
        method: "PATCH",
        body: JSON.stringify(payload)
      }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["workouts", "recent"] }),
        queryClient.invalidateQueries({ queryKey: ["workouts", "strength-overview"] })
      ]);
    }
  });

  function getForm(workout: WorkoutSummary) {
    return forms[workout.id] ?? formFromAnnotation(workout.annotation);
  }

  function updateForm(workout: WorkoutSummary, patch: Partial<FormState>) {
    setForms({ ...forms, [workout.id]: { ...getForm(workout), ...patch } });
  }

  function submit(workout: WorkoutSummary) {
    const form = getForm(workout);
    saveAnnotation.mutate({
      workoutId: workout.id,
      payload: {
        manual_classification: form.manual_classification || null,
        manual_strength_split: form.manual_strength_split || null,
        tag: nullable(form.tag),
        notes: nullable(form.notes)
      }
    });
  }

  return (
    <>
      <PageHeader title="Training Log" eyebrow="Manual Context" />

      {workoutsQuery.isLoading ? <LoadingState message="Loading recent workouts" /> : null}
      {workoutsQuery.isError ? <ErrorState message="Recent workouts are unavailable." /> : null}

      <SectionShell title="Strength Overview">
        <div className="grid gap-4 lg:grid-cols-3">
          <Card>
            <StatBlock
              label="Strength sessions"
              value={String(strengthQuery.data?.strength_sessions ?? 0)}
              hint={strengthQuery.data ? `${formatLongDate(strengthQuery.data.range_start_date)} onward` : "Recent window"}
            />
          </Card>
          <Card>
            <StatBlock
              label="Strength strain"
              value={strengthQuery.data?.strength_strain === null || strengthQuery.data?.strength_strain === undefined ? "—" : String(strengthQuery.data.strength_strain)}
              hint="Sum of tagged or classified strength work"
            />
          </Card>
          <Card>
            <StatBlock
              label="Untagged"
              value={String(strengthQuery.data?.untagged_sessions ?? 0)}
              hint="Strength sessions without a split label"
            />
          </Card>
        </div>
        {strengthQuery.data ? (
          <div className="mt-4 grid gap-3 sm:grid-cols-5">
            {strengthQuery.data.split_counts.map((item) => (
              <Card key={item.split}>
                <StatBlock label={item.split} value={String(item.count)} hint="sessions" />
              </Card>
            ))}
          </div>
        ) : null}
        {strengthQuery.data ? (
          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            <Card>
              <p className="font-semibold">Recent strength weeks</p>
              <div className="mt-3 space-y-2 text-sm">
                {strengthQuery.data.weekly_counts.slice(-6).map((item) => (
                  <div key={item.period_start_date} className="flex justify-between gap-3">
                    <span className="text-muted">{item.label}</span>
                    <span className="font-semibold">{item.count}</span>
                  </div>
                ))}
              </div>
            </Card>
            <Card>
              <p className="font-semibold">Recent strength months</p>
              <div className="mt-3 space-y-2 text-sm">
                {strengthQuery.data.monthly_counts.slice(-6).map((item) => (
                  <div key={item.period_start_date} className="flex justify-between gap-3">
                    <span className="text-muted">{item.label}</span>
                    <span className="font-semibold">{item.count}</span>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        ) : null}
      </SectionShell>

      <SectionShell title="Recent Workouts">
        {workoutsQuery.data?.workouts.length ? (
          <div className="space-y-4">
            {workoutsQuery.data.workouts.map((workout) => {
              const form = getForm(workout);
              const zones = workoutZones(workout);
              const totalZoneSeconds = zones.reduce((total, zone) => total + zone.seconds, 0);
              return (
                <Card key={workout.id}>
                  <div className="grid gap-4 lg:grid-cols-[1.1fr_2fr]">
                    <div>
                      <p className="text-lg font-semibold">{workout.sport_name ?? "Workout"}</p>
                      <p className="mt-1 text-sm text-muted">
                        {formatLongDate(workout.local_start_date)} · {secondsLabel(workout.duration_seconds)}
                      </p>
                      <p className="mt-2 text-sm">
                        {workout.effective_classification} · strain {workout.strain ?? "—"} · HR {workout.average_hr ?? "—"} / {workout.max_hr ?? "—"}
                      </p>
                      <div className="mt-4 grid grid-cols-5 gap-2">
                        {zones.map((zone) => {
                          const key = `zone${zone.zone}` as keyof typeof zoneLabels;
                          const share = totalZoneSeconds > 0 ? (zone.seconds / totalZoneSeconds) * 100 : 0;
                          return (
                            <div key={zone.zone} className="min-w-0 rounded-md border border-line bg-surface/60 p-2">
                              <div className="mb-2 h-1.5 overflow-hidden rounded-sm bg-black/40">
                                <div
                                  className="h-full rounded-sm"
                                  style={{
                                    width: `${zone.seconds > 0 ? Math.max(share, 2) : 0}%`,
                                    background: zoneColors[key]
                                  }}
                                />
                              </div>
                              <p className="text-xs font-semibold">{zoneLabels[key].replace("Zone ", "Z")}</p>
                              <p className="mt-1 text-xs text-muted">{secondsLabel(zone.seconds)}</p>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                    <div className="grid gap-3 lg:grid-cols-2">
                      <label className="grid gap-2 text-sm">
                        Classification
                        <select
                          className="rounded-md border border-line bg-raised px-3 py-2 text-primary"
                          value={form.manual_classification}
                          onChange={(event) => updateForm(workout, { manual_classification: event.target.value as FormState["manual_classification"] })}
                        >
                          <option value="">WHOOP default</option>
                          <option value="cardio">Cardio</option>
                          <option value="strength">Strength</option>
                          <option value="other">Other</option>
                          <option value="unknown">Unknown</option>
                        </select>
                      </label>
                      <label className="grid gap-2 text-sm">
                        Strength split
                        <select
                          className="rounded-md border border-line bg-raised px-3 py-2 text-primary"
                          value={form.manual_strength_split}
                          onChange={(event) => updateForm(workout, { manual_strength_split: event.target.value as FormState["manual_strength_split"] })}
                        >
                          <option value="">Untagged</option>
                          <option value="upper">Upper</option>
                          <option value="lower">Lower</option>
                          <option value="full">Full</option>
                          <option value="unknown">Unknown</option>
                        </select>
                      </label>
                      <label className="grid gap-2 text-sm">
                        Tag
                        <input
                          className="rounded-md border border-line bg-raised px-3 py-2 text-primary"
                          value={form.tag}
                          onChange={(event) => updateForm(workout, { tag: event.target.value })}
                        />
                      </label>
                      <label className="grid gap-2 text-sm">
                        Notes
                        <input
                          className="rounded-md border border-line bg-raised px-3 py-2 text-primary"
                          value={form.notes}
                          onChange={(event) => updateForm(workout, { notes: event.target.value })}
                        />
                      </label>
                      <div className="lg:col-span-2">
                        <Button disabled={saveAnnotation.isPending} onClick={() => submit(workout)}>
                          {saveAnnotation.isPending ? "Saving" : "Save context"}
                        </Button>
                      </div>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        ) : (
          <EmptyState title="No workouts yet" body="Connect WHOOP and run a sync. Recent workouts will land here for tags and notes." />
        )}
      </SectionShell>
    </>
  );
}
