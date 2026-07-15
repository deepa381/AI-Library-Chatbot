import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { authApi } from "../api/auth";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { toast } from "react-hot-toast";
import { BookOpen } from "lucide-react";

export function RegisterPage() {
  const navigate = useNavigate();

  const [loading, setLoading] = useState(false);

  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    username: "",
    email: "",
    phone: "",
    department: "",
    password: "",
    password_confirm: "",
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (formData.password !== formData.password_confirm) {
      toast.error("Passwords do not match");
      return;
    }

    try {
      setLoading(true);

      await authApi.register(formData);

      toast.success("Registration Successful!");

      navigate("/login");
    } catch (err: any) {
      console.error(err.response?.data);

      const errors = err.response?.data;

      if (errors) {
        const firstError = Object.values(errors)[0];

        if (Array.isArray(firstError)) {
          toast.error(firstError[0] as string);
        } else {
          toast.error(String(firstError));
        }
      } else {
        toast.error("Registration failed");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/40 p-4">
      <div className="w-full max-w-md rounded-xl bg-background p-8 shadow-lg border">

        <div className="flex flex-col items-center mb-6">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
            <BookOpen className="h-6 w-6 text-primary" />
          </div>

          <h1 className="text-2xl font-bold mt-4">
            Create an Account
          </h1>

          <p className="text-muted-foreground">
            Join Lumina Library
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">

          <div className="grid grid-cols-2 gap-4">

            <div>
              <label className="text-sm font-medium">
                First Name
              </label>

              <Input
                name="first_name"
                value={formData.first_name}
                onChange={handleChange}
                required
              />
            </div>

            <div>
              <label className="text-sm font-medium">
                Last Name
              </label>

              <Input
                name="last_name"
                value={formData.last_name}
                onChange={handleChange}
                required
              />
            </div>

          </div>

          <div>
            <label className="text-sm font-medium">
              Email
            </label>

            <Input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
            />
          </div>

          <div>
            <label className="text-sm font-medium">
              Username
            </label>

            <Input
              name="username"
              value={formData.username}
              onChange={handleChange}
              required
            />
          </div>

          <div>
            <label className="text-sm font-medium">
              Phone
            </label>

            <Input
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              placeholder="9876543210"
              required
            />
          </div>

          <div>
            <label className="text-sm font-medium">
              Department
            </label>

            <Input
              name="department"
              value={formData.department}
              onChange={handleChange}
              placeholder="CSE"
              required
            />
          </div>

          <div>
            <label className="text-sm font-medium">
              Password
            </label>

            <Input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
            />
          </div>

          <div>
            <label className="text-sm font-medium">
              Confirm Password
            </label>

            <Input
              type="password"
              name="password_confirm"
              value={formData.password_confirm}
              onChange={handleChange}
              required
            />
          </div>

          <Button
            type="submit"
            className="w-full"
            disabled={loading}
          >
            {loading ? "Creating Account..." : "Create Account"}
          </Button>

          <p className="text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link
              to="/login"
              className="text-primary hover:underline"
            >
              Login
            </Link>
          </p>

        </form>

      </div>
    </div>
  );
}