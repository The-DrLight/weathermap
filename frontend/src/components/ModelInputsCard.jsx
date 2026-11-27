import Card from "./Card";

const GROUPS = [
  {
    title: "Current conditions",
    match: (key) =>
      ["temperature_2m", "relative_humidity_2m", "dew_point_2m", "surface_pressure", "cloud_cover", "wind_u", "wind_v"].includes(key),
  },
  { title: "Time of day and year", match: (key) => /^(hour|month)_(sin|cos)$/.test(key) },
  { title: "Recent trends (last 6 h)", match: () => true },
];

function groupFeatures(entries) {
  const groups = GROUPS.map((group) => ({ title: group.title, items: [] }));
  for (const entry of entries) {
    const index = GROUPS.findIndex((group) => group.match(entry[0]));
    groups[index].items.push(entry);
  }
  return groups.filter((group) => group.items.length > 0);
}

export default function ModelInputsCard({ features, className = "" }) {
  const entries = Object.entries(features ?? {});
  if (entries.length === 0) return null;

  return (
    <Card
      title="Model Inputs"
      subtitle={`${entries.length} engineered features fed to the model`}
      className={className}
    >
      <div className="space-y-5">
        {groupFeatures(entries).map(({ title, items }) => (
          <div key={title}>
            <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-subtle">{title}</h3>
            <dl className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
              {items.map(([key, value]) => (
                <div key={key} className="min-w-0 rounded-lg border border-line bg-inset px-3 py-2">
                  <dt className="truncate text-[11px] text-subtle" title={key}>
                    {key}
                  </dt>
                  <dd className="font-mono text-sm tabular-nums text-fg">{value}</dd>
                </div>
              ))}
            </dl>
          </div>
        ))}
      </div>
    </Card>
  );
}
