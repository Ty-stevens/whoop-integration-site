import { Link } from "react-router-dom";

import { Button } from "../components/ui/Button";
import { EmptyState } from "../components/ui/EmptyState";
import { PageHeader } from "../components/ui/PageHeader";

export function NotFoundPage() {
  return (
    <>
      <PageHeader title="Route Not Found" eyebrow="EnduraSync" />
      <EmptyState title="Nothing lives here yet" body="Return to the dashboard and keep training signals in view." />
      <div className="mt-4">
        <Link to="/dashboard">
          <Button>Back to dashboard</Button>
        </Link>
      </div>
    </>
  );
}

