"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiBaseUrl, apiRequest, getToken } from "@/lib/api";

interface ReportResult {
  total: number;
  new: number;
  in_progress: number;
  completed: number;
  rejected: number;
  critical: number;
  avg_processing_hours: number;
}

export default function ReportsPage() {
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [report, setReport] = useState<ReportResult | null>(null);
  const [loading, setLoading] = useState(false);

  async function loadReport() {
    setLoading(true);
    try {
      const data = await apiRequest<ReportResult>("/reports", {
        params: { date_from: dateFrom || undefined, date_to: dateTo || undefined },
      });
      setReport(data);
    } finally {
      setLoading(false);
    }
  }

  function exportFile(format: "csv" | "xlsx") {
    const token = getToken();
    const params = new URLSearchParams();
    if (dateFrom) params.set("date_from", dateFrom);
    if (dateTo) params.set("date_to", dateTo);
    const url = `${apiBaseUrl()}/reports/export.${format}?${params.toString()}`;

    fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      .then((resp) => resp.blob())
      .then((blob) => {
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = `report.${format}`;
        link.click();
      });
  }

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold">Есептер</h1>

      <Card>
        <CardHeader>
          <CardTitle>Кезең бойынша сүзгі</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap items-end gap-4">
          <div className="flex flex-col gap-1.5">
            <Label>Бастап</Label>
            <Input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Дейін</Label>
            <Input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
          </div>
          <Button onClick={loadReport} disabled={loading}>
            Есеп жасау
          </Button>
          <Button variant="outline" onClick={() => exportFile("csv")}>
            CSV экспорт
          </Button>
          <Button variant="outline" onClick={() => exportFile("xlsx")}>
            Excel экспорт
          </Button>
        </CardContent>
      </Card>

      {report && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
          <ReportStat label="Барлығы" value={report.total} />
          <ReportStat label="Жаңа" value={report.new} />
          <ReportStat label="Өңделуде" value={report.in_progress} />
          <ReportStat label="Аяқталды" value={report.completed} />
          <ReportStat label="Қабылданбады" value={report.rejected} />
          <ReportStat label="Авариялық" value={report.critical} />
          <ReportStat label="Орт. өңдеу уақыты (сағ)" value={report.avg_processing_hours} className="col-span-2" />
        </div>
      )}
    </div>
  );
}

function ReportStat({ label, value, className }: { label: string; value: number; className?: string }) {
  return (
    <Card className={className}>
      <CardContent className="p-4">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="mt-1 text-xl font-bold">{value}</p>
      </CardContent>
    </Card>
  );
}
