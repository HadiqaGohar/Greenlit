"use client";

import { useState } from "react";

interface Character {
  name: string;
  descriptions: string[];
  first_appearance: number;
  total_scenes: number;
  character_type: "lead" | "supporting" | "recurring" | "background";
  age_range?: string;
  gender?: string;
  relationships: Record<string, string>;
}

interface CharacterBibleProps {
  characters: Character[];
}

const typeColors: Record<string, string> = {
  lead: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300",
  supporting: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300",
  recurring: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300",
  background: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
};

const typeIcons: Record<string, string> = {
  lead: "⭐",
  supporting: "🎭",
  recurring: "👤",
  background: "👥",
};

export function CharacterBible({ characters }: CharacterBibleProps) {
  const [selectedCharacter, setSelectedCharacter] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"grid" | "relationships">("grid");

  if (characters.length === 0) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-900">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Character Bible
        </h3>
        <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
          No character data available. Analyze a script to see character profiles.
        </p>
      </div>
    );
  }

  const leads = characters.filter((c) => c.character_type === "lead");
  const supporting = characters.filter((c) => c.character_type === "supporting");

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-900">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Character Bible
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {characters.length} characters · {leads.length} leads ·{" "}
            {supporting.length} supporting
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setViewMode("grid")}
            className={`rounded-lg px-3 py-1.5 text-sm ${
              viewMode === "grid"
                ? "bg-blue-600 text-white"
                : "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300"
            }`}
          >
            Profiles
          </button>
          <button
            onClick={() => setViewMode("relationships")}
            className={`rounded-lg px-3 py-1.5 text-sm ${
              viewMode === "relationships"
                ? "bg-blue-600 text-white"
                : "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300"
            }`}
          >
            Relationships
          </button>
        </div>
      </div>

      {viewMode === "grid" ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {characters.map((char) => {
            const isSelected = selectedCharacter === char.name;
            return (
              <div
                key={char.name}
                onClick={() =>
                  setSelectedCharacter(isSelected ? null : char.name)
                }
                className={`cursor-pointer rounded-lg border p-4 transition-all ${
                  isSelected
                    ? "border-blue-500 ring-2 ring-blue-200 dark:ring-blue-800"
                    : "border-gray-200 hover:border-gray-300 dark:border-gray-700 dark:hover:border-gray-600"
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">{typeIcons[char.character_type]}</span>
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white">
                        {char.name}
                      </h4>
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                          typeColors[char.character_type]
                        }`}
                      >
                        {char.character_type}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Details */}
                <div className="mt-3 space-y-1 text-xs text-gray-500 dark:text-gray-400">
                  <p>First appears: Scene {char.first_appearance}</p>
                  <p>Total scenes: {char.total_scenes}</p>
                  {char.age_range && <p>Age: {char.age_range}</p>}
                  {char.gender && <p>Gender: {char.gender}</p>}
                </div>

                {/* Descriptions */}
                {char.descriptions.length > 0 && (
                  <div className="mt-3">
                    <p className="text-xs font-medium text-gray-700 dark:text-gray-300">
                      Description:
                    </p>
                    <p className="mt-1 text-xs text-gray-600 dark:text-gray-400">
                      {char.descriptions[0]}
                    </p>
                  </div>
                )}

                {/* Expanded: Relationships */}
                {isSelected && Object.keys(char.relationships).length > 0 && (
                  <div className="mt-3 border-t border-gray-200 pt-3 dark:border-gray-700">
                    <p className="text-xs font-medium text-gray-700 dark:text-gray-300">
                      Relationships:
                    </p>
                    <div className="mt-1 space-y-1">
                      {Object.entries(char.relationships).map(([name, rel]) => (
                        <p key={name} className="text-xs text-gray-600 dark:text-gray-400">
                          → {name}: <span className="italic">{rel}</span>
                        </p>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        /* Relationship Map View */
        <div className="rounded-lg bg-gray-50 p-6 dark:bg-gray-800">
          <div className="flex flex-wrap justify-center gap-8">
            {leads.map((char) => (
              <div key={char.name} className="text-center">
                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-purple-100 text-2xl dark:bg-purple-900/30">
                  ⭐
                </div>
                <p className="mt-2 text-sm font-medium text-gray-900 dark:text-white">
                  {char.name}
                </p>
                <div className="mt-1 space-y-0.5">
                  {Object.entries(char.relationships).map(([name, rel]) => (
                    <p key={name} className="text-xs text-gray-500 dark:text-gray-400">
                      {rel} → {name}
                    </p>
                  ))}
                </div>
              </div>
            ))}
          </div>
          {supporting.length > 0 && (
            <>
              <div className="my-4 border-t border-gray-200 dark:border-gray-700" />
              <div className="flex flex-wrap justify-center gap-6">
                {supporting.map((char) => (
                  <div key={char.name} className="text-center">
                    <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-100 text-xl dark:bg-blue-900/30">
                      🎭
                    </div>
                    <p className="mt-1 text-xs font-medium text-gray-900 dark:text-white">
                      {char.name}
                    </p>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
