import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Login from "../../pages/Login";
import * as AuthContextModule from "../../contexts/AuthContext";

const mockNavigate = jest.fn();
jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => mockNavigate,
}));

jest.mock("../../contexts/AuthContext", () => ({
  ...jest.requireActual("../../contexts/AuthContext"),
  useAuth: jest.fn(),
}));

describe("Login", () => {
  const mockLogin = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    AuthContextModule.useAuth.mockReturnValue({
      login: mockLogin,
    });
  });

  it("renders login form", () => {
    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>,
    );

    expect(screen.getByLabelText(/user name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /sign in/i }),
    ).toBeInTheDocument();
    expect(screen.getByText("Learning App")).toBeInTheDocument();
  });

  it("submits credentials", async () => {
    mockLogin.mockResolvedValue({ success: true });

    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByLabelText(/user name/i), {
      target: { value: "testuser" },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: "testpass" },
    });
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith("testuser", "testpass");
    });

    expect(mockNavigate).toHaveBeenCalledWith("/chat");
  });

  it("shows error on failed login", async () => {
    mockLogin.mockResolvedValue({
      success: false,
      message: "Invalid credentials",
    });

    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByLabelText(/user name/i), {
      target: { value: "testuser" },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: "wrongpass" },
    });
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText("Invalid credentials")).toBeInTheDocument();
    });
  });
});
