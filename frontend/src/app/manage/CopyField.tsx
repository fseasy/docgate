// components/CopyField.tsx
import { useClipboard, type CopyStatus } from "../../utils/frontendHooks";

interface CopyFieldProps {
  label: string;
  value: string;
  disabled?: boolean;
  size?: "sm" | "default";
  timeout?: number;
}

export function CopyField({
  label,
  value,
  disabled = false,
  size = "default",
  timeout = 2000
}: CopyFieldProps) {
  const { copyStatus, copyToClipboard } = useClipboard({ timeout });

  const handleCopy = () => {
    copyToClipboard(value);
  };

  const btnClass = size === "sm"
    ? "btn btn-info btn-soft btn-xs"
    : "btn btn-info btn-soft";

  const statusText: Record<CopyStatus, string> = {
    idle: "复制",
    success: "已复制 ✓",
    fail: "失败 ✕"
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-5">
        <label className="text-sm text-base-content">{label}</label>
        <button
          className={btnClass}
          onClick={handleCopy}
          disabled={disabled || !value}
        >
          {statusText[copyStatus]}
        </button>
      </div>
      <code className="block font-mono text-sm bg-base-200 rounded px-3 py-2 break-all">
        {value || "—"}
      </code>
    </div>
  );
}