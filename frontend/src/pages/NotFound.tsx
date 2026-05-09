import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <div className="space-y-4 py-12 text-center">
      <p className="text-6xl font-bold text-muted-foreground">404</p>
      <p className="text-lg font-medium">페이지를 찾을 수 없습니다</p>
      <Link
        to="/"
        className="inline-flex h-9 items-center justify-center rounded-md border border-input bg-background px-4 text-sm font-medium hover:bg-accent hover:text-accent-foreground"
      >
        대시보드로 돌아가기
      </Link>
    </div>
  );
}
