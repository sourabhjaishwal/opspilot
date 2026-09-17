import { useEffect, useState } from "react";
import { getHealth } from "../api/client";

function HealthStatus({ onStatusChange }) {
  const [status, setStatus] = useState("checking");

  useEffect(() => {
    let active = true;
    getHealth()
      .then((response) => {
        if (!active) return;
        const nextStatus =
          response.status === "healthy" ? "healthy" : "degraded";
        setStatus(nextStatus);
        onStatusChange(nextStatus);
      })
      .catch(() => {
        if (!active) return;
        setStatus("offline");
        onStatusChange("offline");
      });
    return () => {
      active = false;
    };
  }, [onStatusChange]);

  return (
    <div className={`connection-state ${status}`}>
      <span className="status-dot" />
      API {status}
    </div>
  );
}

export default HealthStatus;
