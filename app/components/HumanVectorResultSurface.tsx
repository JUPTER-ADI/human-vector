type JsonRecord = Record<string, unknown>;

function isRecord(value: unknown): value is JsonRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function findValue(
  value: unknown,
  keys: readonly string[],
  depth = 0,
): unknown {
  if (depth > 8) return undefined;

  if (isRecord(value)) {
    for (const key of keys) {
      if (key in value) return value[key];
    }

    for (const child of Object.values(value)) {
      const found = findValue(child, keys, depth + 1);
      if (found !== undefined) return found;
    }
  }

  if (Array.isArray(value)) {
    for (const child of value) {
      const found = findValue(child, keys, depth + 1);
      if (found !== undefined) return found;
    }
  }

  return undefined;
}

function textValue(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function numberValue(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function textList(value: unknown): string[] {
  if (typeof value === "string" && value.trim()) return [value.trim()];

  if (Array.isArray(value)) {
    return value
      .filter((item): item is string => typeof item === "string")
      .map((item) => item.trim())
      .filter(Boolean);
  }

  return [];
}

export default function HumanVectorResultSurface({
  data,
}: {
  data: unknown;
}) {
  const decision = textValue(
    findValue(data, [
      "selector_final_decision",
      "selector_decision",
      "decision",
    ]),
  );

  const rounds = numberValue(
    findValue(data, [
      "selector_rounds",
      "canonical_selector_rounds",
    ]),
  );

  const reconstructions = numberValue(
    findValue(data, [
      "selector_reconstruction_count",
      "reconstruction_count",
    ]),
  );

  const reasons = textList(
    findValue(data, [
      "selector_reasons",
      "reasons",
    ]),
  );

  const requirements = textList(
    findValue(data, [
      "reconstruction_requirements",
      "selector_reconstruction_requirements",
    ]),
  );

  return (
    <div>
      <h3>HUMAN VECTOR — rezultat verificat</h3>

      <p>
        <strong>Selector Canonic:</strong>{" "}
        {decision ?? "stare disponibilă în rezultatul tehnic"}
      </p>

      {rounds !== null && (
        <p>
          <strong>Evaluări Selector:</strong> {rounds}
        </p>
      )}

      {reconstructions !== null && (
        <p>
          <strong>Reconstrucții Builder:</strong> {reconstructions}
        </p>
      )}

      {decision === "PASS" && (
        <p>
          Rezultatul a trecut verificarea Selectorului Canonic și este
          disponibil HUMAN.
        </p>
      )}

      {decision === "RECONSTRUCT" && (
        <p>
          Builder reconstruiește rezultatul, iar noua versiune revine
          obligatoriu la Selector.
        </p>
      )}


      <details>
        <summary>Detalii tehnice și proveniență</summary>
        <pre>{JSON.stringify(data, null, 2)}</pre>
      </details>
    </div>
  );
}
