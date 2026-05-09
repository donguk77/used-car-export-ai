import { Construction } from "lucide-react";
import type { ReactNode } from "react";

import { Card, CardContent } from "@/components/ui/card";

export function PageStub({
  title,
  subtitle,
  next,
}: {
  title: string;
  subtitle?: string;
  next?: ReactNode;
}) {
  return (
    <div className="space-y-6">
      <header>
        <h2 className="text-2xl font-semibold tracking-tight">{title}</h2>
        {subtitle && <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>}
      </header>
      <Card>
        <CardContent className="flex items-center gap-4 py-12">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-warning/15">
            <Construction className="h-6 w-6 text-warning" />
          </div>
          <div>
            <p className="font-medium">곧 채워집니다</p>
            <p className="text-sm text-muted-foreground">{next ?? "Day 2 ~ Day 5 에 구현 예정"}</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
