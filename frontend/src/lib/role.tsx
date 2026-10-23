import React, { createContext, useContext, useState } from "react"

export type UserRole = "company" | "customer"

export interface RoleContextValue {
  role: UserRole | null
  setRole: (role: UserRole) => void
  clearRole: () => void
}

export const ROLE_STORAGE_KEY = "complaint_intelligence_role"

const RoleContext = createContext<RoleContextValue | undefined>(undefined)

export function RoleProvider({ children }: { children: React.ReactNode }) {
  const [role, setRoleState] = useState<UserRole | null>(() => {
    try {
      const saved = localStorage.getItem(ROLE_STORAGE_KEY)
      if (saved === "company" || saved === "customer") {
        return saved
      }
    } catch {
      // LocalStorage access may fail in private mode
    }
    return null
  })

  const setRole = (newRole: UserRole) => {
    try {
      localStorage.setItem(ROLE_STORAGE_KEY, newRole)
    } catch {
      // Ignore write errors
    }
    setRoleState(newRole)
  }

  const clearRole = () => {
    try {
      localStorage.removeItem(ROLE_STORAGE_KEY)
    } catch {
      // Ignore remove errors
    }
    setRoleState(null)
  }

  return (
    <RoleContext.Provider value={{ role, setRole, clearRole }}>
      {children}
    </RoleContext.Provider>
  )
}

export function useRole(): RoleContextValue {
  const context = useContext(RoleContext)
  if (!context) {
    throw new Error("useRole must be used within a RoleProvider")
  }
  return context
}
