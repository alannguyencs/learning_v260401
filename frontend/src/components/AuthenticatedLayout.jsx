import React from "react";
import { Outlet } from "react-router-dom";
import BottomNavBar from "./BottomNavBar";

const AuthenticatedLayout = () => (
  <div className="flex flex-col min-h-screen">
    <div className="flex-1 pb-16">
      <Outlet />
    </div>
    <div className="fixed bottom-0 left-0 right-0 z-40">
      <BottomNavBar />
    </div>
  </div>
);

export default AuthenticatedLayout;
