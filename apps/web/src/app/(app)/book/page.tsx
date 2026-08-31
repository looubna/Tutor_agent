import { redirect } from "next/navigation";

/** Booking always starts from a subject now, so send people to the catalogue. */
export default function BookPage() {
  redirect("/book/languages");
}
