import Link from "next/link";
export default function Page() {
  return (
    <main className="p-6">
      <h1 className="text-2xl font-semibold mb-4">Dashboard</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <Link href="/calc" className="border rounded-2xl p-6 hover:shadow">
          <div className="text-lg font-medium">Калькулятор</div>
          <div className="text-sm text-gray-500">Розрахунок з довідниками</div>
        </Link>
      </div>
    </main>
  );
}
