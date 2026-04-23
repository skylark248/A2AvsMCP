import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import LinkOutlinedIcon from "@mui/icons-material/LinkOutlined";
import { Box, Button, Card, CardContent, Stack, Typography } from "@mui/material";
import { useMemo } from "react";

import { useAppUi } from "../../app/ui/AppUiProvider";

interface MetricBarItem {
  label: string;
  value: number;
  displayValue?: string;
  color?: string;
  subtitle?: string;
}

interface MetricBarsCardProps {
  title: string;
  subtitle?: string;
  items: MetricBarItem[];
  inverse?: boolean;
  minBarPercent?: number;
  snapshotKey?: string;
}

function slugify(value: string) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

function escapeXml(value: string) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&apos;");
}

export function MetricBarsCard({
  title,
  subtitle,
  items,
  inverse = false,
  minBarPercent = 8,
  snapshotKey,
}: MetricBarsCardProps) {
  const { showToast } = useAppUi();
  const numericValues = items.map((item) => item.value);
  const min = numericValues.length > 0 ? Math.min(...numericValues) : 0;
  const max = numericValues.length > 0 ? Math.max(...numericValues) : 0;
  const anchorId = useMemo(() => snapshotKey ?? slugify(title), [snapshotKey, title]);

  function barPercent(value: number) {
    if (max === min) {
      return 72;
    }
    const normalized = inverse ? (max - value) / (max - min) : (value - min) / (max - min);
    return Math.max(minBarPercent, Math.min(100, Math.round(minBarPercent + normalized * (100 - minBarPercent))));
  }

  function buildSnapshotSvg() {
    const width = 1200;
    const headerHeight = subtitle ? 142 : 112;
    const rowHeight = 92;
    const padding = 52;
    const chartWidth = width - padding * 2;
    const height = headerHeight + items.length * rowHeight + 48;

    const rows = items
      .map((item, index) => {
        const top = headerHeight + index * rowHeight;
        const widthPx = Math.round((chartWidth * barPercent(item.value)) / 100);
        return `
      <text x="${padding}" y="${top}" font-size="28" font-family="Segoe UI, Arial, sans-serif" fill="#102033">${escapeXml(item.label)}</text>
      <text x="${width - padding}" y="${top}" text-anchor="end" font-size="26" font-family="Segoe UI, Arial, sans-serif" fill="#4f5d75">${escapeXml(item.displayValue ?? String(item.value))}</text>
      <rect x="${padding}" y="${top + 18}" width="${chartWidth}" height="22" rx="11" fill="#edf1f3" />
      <rect x="${padding}" y="${top + 18}" width="${widthPx}" height="22" rx="11" fill="${item.color ?? "#17475f"}" />
      ${item.subtitle ? `<text x="${padding}" y="${top + 70}" font-size="22" font-family="Segoe UI, Arial, sans-serif" fill="#4f5d75">${escapeXml(item.subtitle)}</text>` : ""}`;
      })
      .join("");

    return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
  <rect width="${width}" height="${height}" rx="28" fill="#fffaf4" />
  <text x="${padding}" y="58" font-size="38" font-weight="700" font-family="Segoe UI, Arial, sans-serif" fill="#17475f">${escapeXml(title)}</text>
  ${subtitle ? `<text x="${padding}" y="96" font-size="24" font-family="Segoe UI, Arial, sans-serif" fill="#4f5d75">${escapeXml(subtitle)}</text>` : ""}
  ${rows}
</svg>`;
  }

  function handleDownload() {
    const svg = buildSnapshotSvg();
    const blob = new Blob([svg], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${anchorId || "chart-snapshot"}.svg`;
    link.click();
    URL.revokeObjectURL(url);
    showToast({ message: "SVG snapshot downloaded.", severity: "success" });
  }

  async function handleShare() {
    const shareUrl = `${window.location.href.split("#")[0]}#${anchorId}`;
    try {
      await navigator.clipboard.writeText(shareUrl);
      showToast({ message: "Chart link copied to clipboard.", severity: "success" });
    } catch {
      showToast({ message: `Copy this chart link: ${shareUrl}`, severity: "info" });
    }
  }

  return (
    <Card id={anchorId} sx={{ height: "100%", scrollMarginTop: 112 }}>
      <CardContent>
        <Stack spacing={1.5}>
          <Stack direction={{ xs: "column", sm: "row" }} justifyContent="space-between" spacing={1.5}>
            <Stack spacing={0.5}>
              <Typography variant="h6">{title}</Typography>
              {subtitle ? (
                <Typography variant="body2" sx={{ color: "text.secondary" }}>
                  {subtitle}
                </Typography>
              ) : null}
            </Stack>
            <Stack direction="row" spacing={1} sx={{ flexShrink: 0 }}>
              <Button
                size="small"
                variant="text"
                startIcon={<LinkOutlinedIcon fontSize="small" />}
                onClick={() => void handleShare()}
              >
                Share
              </Button>
              <Button
                size="small"
                variant="text"
                startIcon={<DownloadOutlinedIcon fontSize="small" />}
                onClick={handleDownload}
              >
                Snapshot
              </Button>
            </Stack>
          </Stack>
          <Stack spacing={1.25}>
            {items.map((item) => (
              <Stack key={`${title}-${item.label}`} spacing={0.5}>
                <Stack direction="row" justifyContent="space-between" spacing={1}>
                  <Typography variant="body2">{item.label}</Typography>
                  <Typography variant="body2" sx={{ color: "text.secondary" }}>
                    {item.displayValue ?? String(item.value)}
                  </Typography>
                </Stack>
                <Box sx={{ height: 10, borderRadius: 999, bgcolor: "rgba(23, 71, 95, 0.08)", overflow: "hidden" }}>
                  <Box
                    sx={{
                      width: `${barPercent(item.value)}%`,
                      height: "100%",
                      borderRadius: 999,
                      background: item.color ?? "linear-gradient(90deg, #17475f, #b85c38)",
                    }}
                  />
                </Box>
                {item.subtitle ? (
                  <Typography variant="caption" sx={{ color: "text.secondary" }}>
                    {item.subtitle}
                  </Typography>
                ) : null}
              </Stack>
            ))}
          </Stack>
        </Stack>
      </CardContent>
    </Card>
  );
}
