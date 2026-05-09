import { AlertOctagon } from "lucide-react";
import { Link, isRouteErrorResponse, useRouteError } from "react-router-dom";

import { Card, CardContent } from "@/components/ui/card";

/** React Router root errorElement — 렌더 에러 시 흰화면 대신 표시. */
export function RouteErrorPage() {
  const error = useRouteError();

  let title = "예기치 않은 오류";
  let detail = "";

  if (isRouteErrorResponse(error)) {
    if (error.status === 404) {
      title = "페이지를 찾을 수 없습니다";
    } else {
      title = `${error.status} ${error.statusText}`;
      detail = typeof error.data === "string" ? error.data : JSON.stringify(error.data);
    }
  } else if (error instanceof Error) {
    detail = error.message;
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/30 p-6">
      <Card className="max-w-md">
        <CardContent className="space-y-4 py-10 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
            <AlertOctagon className="h-6 w-6 text-destructive" />
          </div>
          <div className="space-y-1">
            <p className="text-lg font-semibold">{title}</p>
            {detail && (
              <p className="break-all text-xs text-muted-foreground">{detail}</p>
            )}
          </div>
          <Link
            to="/"
            className="inline-flex h-9 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            대시보드로 돌아가기
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
