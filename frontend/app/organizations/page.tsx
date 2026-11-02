"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

type User = { id: string; email: string; display_name: string; organization_id: string; organization_name: string; role: string; is_active: boolean };
type Organization = { organization_id: string; organization_name: string; role: string; is_current: boolean };
type Member = { id: string; email: string; display_name: string; role: string; membership_status: string; created_at: string };

export default function OrganizationsPage() {
  const [token, setToken] = useState("");
  const [user, setUser] = useState<User | null>(null);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [members, setMembers] = useState<Member[]>([]);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [memberEmail, setMemberEmail] = useState("");
  const [memberRole, setMemberRole] = useState("researcher");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function request(path: string, accessToken: string, init: RequestInit = {}) {
    const response = await fetch(API + path, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer " + accessToken,
        ...(init.headers || {}),
      },
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Request failed.");
    return data;
  }

  async function loadWorkspace(accessToken: string) {
    const [orgData, memberData] = await Promise.all([
      request("/api/v1/auth/organizations", accessToken),
      request("/api/v1/organizations/members", accessToken),
    ]);
    setOrganizations(orgData.items || []);
    setMembers(memberData.members || []);
    const current = (orgData.items || []).find((item: Organization) => item.is_current);
    if (current) {
      const me = await request("/api/v1/auth/me", accessToken);
      setUser(me);
    }
  }

  async function signIn(event: FormEvent) {
    event.preventDefault();
    setBusy(true); setError(""); setNotice("");
    try {
      const response = await fetch(API + "/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Sign in failed.");
      setToken(data.access_token); setUser(data.user); setPassword("");
      await loadWorkspace(data.access_token);
      setNotice("Signed in. Your organisation memberships are loaded.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Sign in failed.");
    } finally { setBusy(false); }
  }

  async function switchOrganization(organizationId: string) {
    setBusy(true); setError(""); setNotice("");
    try {
      const data = await request("/api/v1/auth/switch-organization", token, {
        method: "POST", body: JSON.stringify({ organization_id: organizationId }),
      });
      setToken(data.access_token); setUser(data.user);
      await loadWorkspace(data.access_token);
      setNotice("Active organisation changed. New requests now use the selected organisation.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not switch organisation.");
    } finally { setBusy(false); }
  }

  async function addMember(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError(""); setNotice("");
    try {
      const data = await request("/api/v1/organizations/members", token, {
        method: "POST", body: JSON.stringify({ email: memberEmail, role: memberRole }),
      });
      setMemberEmail("");
      await loadWorkspace(token);
      setNotice(data.message || "Member added.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not add member.");
    } finally { setBusy(false); }
  }

  async function updateRole(memberId: string, role: string) {
    setBusy(true); setError(""); setNotice("");
    try {
      await request("/api/v1/organizations/members/" + memberId + "/role", token, {
        method: "PATCH", body: JSON.stringify({ role }),
      });
      await loadWorkspace(token);
      setNotice("Member role updated and audit event recorded.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not update member role.");
    } finally { setBusy(false); }
  }

  const isAdmin = user?.role === "organization_admin";

  return <main className="container min-h-screen py-10">
    <Link href="/" className="text-sm text-emerald-300">← Toolkit home</Link>
    <header className="mt-8 max-w-3xl">
      <p className="accent text-xs tracking-[.2em]">ORGANISATION ACCESS & GOVERNANCE</p>
      <h1 className="mt-3 text-4xl font-semibold">Organisation workspace</h1>
      <p className="muted mt-4 text-sm leading-7">Manage existing registered members, select the organisation for this session and assign research or review roles. Membership changes are recorded in the audit trail.</p>
    </header>

    {error && <p role="alert" className="mt-5 rounded-xl border border-rose-400/30 p-4 text-sm text-rose-200">{error}</p>}
    {notice && <p role="status" className="mt-5 rounded-xl border border-emerald-400/30 p-4 text-sm text-emerald-200">{notice}</p>}

    {!token ? <section className="panel mt-7 max-w-xl p-6">
      <h2 className="text-xl font-semibold">Sign in to manage your organisation</h2>
      <form onSubmit={signIn} className="mt-5 space-y-4">
        <label className="block"><span className="muted text-xs">Email</span><input className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-3 text-sm" type="email" required value={email} onChange={e => setEmail(e.target.value)} /></label>
        <label className="block"><span className="muted text-xs">Password</span><input className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-3 text-sm" type="password" required value={password} onChange={e => setPassword(e.target.value)} /></label>
        <button disabled={busy} className="rounded-full bg-emerald-400 px-5 py-3 text-sm font-semibold text-slate-950 disabled:opacity-50">{busy ? "Signing in…" : "Sign in"}</button>
      </form>
    </section> : <>
      <section className="panel mt-7 p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div><p className="muted text-xs">ACTIVE ORGANISATION</p><h2 className="mt-1 text-2xl font-semibold">{user?.organization_name || "Loading…"}</h2><p className="muted mt-1 text-sm">{user?.display_name} · {user?.role}</p></div>
          <button onClick={() => { setToken(""); setUser(null); setOrganizations([]); setMembers([]); setNotice("Signed out."); }} className="rounded-full border border-slate-600 px-4 py-2 text-xs">Sign out</button>
        </div>
        {organizations.length > 1 && <div className="mt-6"><h3 className="text-sm font-semibold">Switch organisation</h3><div className="mt-3 flex flex-wrap gap-2">{organizations.map(org => <button key={org.organization_id} disabled={busy || org.is_current} onClick={() => void switchOrganization(org.organization_id)} className={"rounded-full border px-4 py-2 text-xs disabled:opacity-50 " + (org.is_current ? "border-emerald-400/60 text-emerald-300" : "border-slate-600 text-slate-300")}>{org.organization_name} · {org.role}</button>)}</div></div>}
      </section>

      <section className="panel mt-6 p-6">
        <div className="flex flex-wrap items-end justify-between gap-3"><div><h2 className="text-xl font-semibold">Members ({members.length})</h2><p className="muted mt-1 text-sm">Active organisation membership only.</p></div></div>
        <div className="mt-5 space-y-3">{members.map(member => <div key={member.id} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-700 p-4">
          <div><p className="text-sm font-medium">{member.display_name}</p><p className="muted mt-1 text-xs">{member.email} · {member.membership_status}</p></div>
          {isAdmin && member.id !== user?.id ? <select aria-label={"Role for " + member.email} disabled={busy} value={member.role} onChange={e => void updateRole(member.id, e.target.value)} className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs"><option value="curator">Curator</option><option value="reviewer">Reviewer</option><option value="researcher">Researcher</option><option value="viewer">Viewer</option></select> : <span className="rounded-full border border-slate-700 px-3 py-1 text-xs">{member.role}</span>}
        </div>)}</div>
      </section>

      {isAdmin && <section className="panel mt-6 max-w-2xl p-6">
        <h2 className="text-xl font-semibold">Add an existing account</h2>
        <p className="muted mt-2 text-sm leading-6">The person must register for Toolkit first. Enter the same account email, then assign the minimum role they need. This action adds the account immediately; it does not send an email invitation.</p>
        <form onSubmit={addMember} className="mt-5 grid gap-4 sm:grid-cols-[1fr_180px_auto] sm:items-end">
          <label className="block"><span className="muted text-xs">Registered account email</span><input className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-3 text-sm" type="email" required value={memberEmail} onChange={e => setMemberEmail(e.target.value)} /></label>
          <label className="block"><span className="muted text-xs">Organisation role</span><select className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-3 text-sm" value={memberRole} onChange={e => setMemberRole(e.target.value)}><option value="researcher">Researcher</option><option value="reviewer">Reviewer</option><option value="curator">Curator</option><option value="viewer">Viewer</option></select></label>
          <button disabled={busy} className="rounded-full bg-emerald-400 px-5 py-3 text-sm font-semibold text-slate-950 disabled:opacity-50">Add member</button>
        </form>
      </section>}
    </>}
  </main>;
}
