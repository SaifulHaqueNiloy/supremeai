import { useEffect, useState } from "react";
import { useAdminStore } from "../../store/adminStore";
import { AdminConsole } from "../../components/admin/AdminConsole";
import { apiClient } from "../../services/apiClient";
import { Shield } from "lucide-react";
import type { AdminSubTab, Skill, Checkpoint, ChatMessage, HealthMap } from "../../types";
import { useCostReport, useHealthMap, useSkills, useCheckpoints, useDeleteCheckpoint, useInstallSkill } from "../../hooks";
import { useTheme } from "../../contexts/useTheme";

export function AdminShell() {
  const {
    adminAuthenticated,
    adminRole,
    adminEmail,
    setAdminEmail,
    adminError,
    handleAdminLogin,
    otpRequired,
    adminOtp,
    setAdminOtp,
    totpSetupRequired,
    provisioningUri,
    totpSecret,
    handleAdminLogout,
    actionStatus,
    setActionStatus,
    resetTotpSetup,
  } = useAdminStore();

  const [adminSubTab, setAdminSubTab] = useState<AdminSubTab>("overview");
  const [skillQuery, setSkillQuery] = useState("");
  
  const { data: skillsList = [] } = useSkills(skillQuery);
  const { data: checkpointsList = [] } = useCheckpoints();
  const { data: costReportData } = useCostReport();
  const costReport = costReportData?.report || "";
  const { data: healthMapData } = useHealthMap();
  const healthMap = healthMapData || { gcp: { status: 'unknown', latency: '', region: '' }, railway: { status: 'unknown', latency: '', region: '' }, render: { status: 'unknown', latency: '', region: '' } };

  const [adminMessages] = useState<ChatMessage[]>([]);
  const [loading] = useState(false);
  const [saveStatus, setSaveStatus] = useState("");
  const [liveLogs, setLiveLogs] = useState<string[]>([]);
  const [newUsername, setNewUsername] = useState("");
  const [newUserRole, setNewUserRole] = useState("Operator");
  const [newUserPerms, setNewUserPerms] = useState("read,write");
  const [adminInput, setAdminInput] = useState("");
  const [rulesJson, setRulesJson] = useState("");

  // বাংলা (single-frontend migration): আগে এখানে আলাদা useState theme +
  // documentElement.classList effect ছিল — এটি shared ThemeProvider-এর সাথে
  // একই <html> class attribute নিয়ে লড়ত (duplicate theme authority)। এখন
  // একক ThemeProvider-ই owner; AdminShell শুধু consume করে।
  // AdminConsole-এর interface 'dark'|'light' প্রত্যাশা করে — 4-theme value
  // থেকে সামঞ্জস্যপূর্ণ mapping করা হলো (UI preview-only usage)।
  const { theme, toggleTheme } = useTheme();
  const consoleTheme: 'dark' | 'light' = theme === 'light' ? 'light' : 'dark';

  useEffect(() => {
    if (!adminAuthenticated) return;

    if (adminRole !== 'admin') {
      if (import.meta.env.DEV) console.warn("RBAC: User is not an admin.");
    }

  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [adminAuthenticated]);

  const handleAdminOtpVerify = () => {
    handleAdminLogin();
  };

  const handleResetTotp = () => {
    resetTotpSetup();
  };

  const installSkillMutation = useInstallSkill();
  const handleInstallSkill = (name: string) => {
    installSkillMutation.mutate(name);
  };

  const deleteCheckpointMutation = useDeleteCheckpoint();
  const handleDeleteCheckpoint = (taskId: string) => {
    deleteCheckpointMutation.mutate(taskId);
  };

  const handleTriggerDeploy = () => {
    setActionStatus("TRIGGERING DEPLOY...");
    apiClient.post('/admin-api/deploy')
      .then(() => {
        setActionStatus("DEPLOY TRIGGERED");
        setTimeout(() => setActionStatus(""), 2000);
      })
      .catch(() => {
        setActionStatus("DEPLOY FAILED");
        setTimeout(() => setActionStatus(""), 2000);
      });
  };

  const handleSendAdmin = () => {
    if (import.meta.env.DEV) console.warn("Send admin message", adminInput);
    setAdminInput("");
  };

  const handleSaveRules = () => {
    setSaveStatus("SAVING...");
    setTimeout(() => setSaveStatus("SAVED"), 1000);
  };

  if (adminAuthenticated && adminRole !== 'admin') {
    return (
      <div className="flex h-screen bg-[#0A0A0A] text-white items-center justify-center font-sans">
        <div className="w-[400px] p-8 rounded-2xl bg-white/5 border border-red-500/30 text-center flex flex-col items-center gap-4">
          <Shield className="w-16 h-16 text-red-500" />
          <h1 className="text-2xl font-semibold">Access Denied</h1>
          <p className="text-sm text-gray-400">You do not have the required "admin" role to access this dashboard.</p>
          <button
            onClick={handleAdminLogout}
            className="mt-4 px-6 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 font-medium rounded-lg transition-colors border border-red-500/50"
          >
            Logout
          </button>
        </div>
      </div>
    );
  }

  return (
    <AdminConsole
      adminAuthenticated={adminAuthenticated}
      adminEmail={adminEmail}
      setAdminEmail={setAdminEmail}
      totpSetupRequired={totpSetupRequired}
      provisioningUri={provisioningUri}
      totpSecret={totpSecret}
      onResetTotp={handleResetTotp}
      adminError={adminError}
      handleAdminLogin={handleAdminLogin}
      handleAdminOtpVerify={handleAdminOtpVerify}
      handleAdminLogout={handleAdminLogout}
      actionStatus={actionStatus}
      skillQuery={skillQuery}
      setSkillQuery={setSkillQuery}
      skills={skillsList}
      handleInstallSkill={handleInstallSkill}
      checkpoints={checkpointsList}
      handleDeleteCheckpoint={handleDeleteCheckpoint}
      adminSubTab={adminSubTab}
      setAdminSubTab={setAdminSubTab}
      handleTriggerDeploy={handleTriggerDeploy}
      adminMessages={adminMessages}
      loading={loading}
      adminInput={adminInput}
      setAdminInput={setAdminInput}
      handleSendAdmin={handleSendAdmin}
      rulesJson={rulesJson}
      setRulesJson={setRulesJson}
      saveStatus={saveStatus}
      handleSaveRules={handleSaveRules}
      liveLogs={liveLogs}
      setLiveLogs={setLiveLogs}
      costReport={costReport}
      healthMap={healthMap}
      newUsername={newUsername}
      setNewUsername={setNewUsername}
      newUserRole={newUserRole}
      setNewUserRole={setNewUserRole}
      newUserPerms={newUserPerms}
      setNewUserPerms={setNewUserPerms}
      otpRequired={otpRequired}
      adminOtp={adminOtp}
      setAdminOtp={setAdminOtp}
      theme={consoleTheme}
      toggleTheme={toggleTheme}
    />
  );
}
