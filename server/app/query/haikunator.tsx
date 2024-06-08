import Haikunator from "haikunator";
import { nouns, adjectives } from "./words";

const haikunator = new Haikunator({
  adjectives: adjectives,
  nouns: nouns,
});

function getCurrentTimestamp()  {
    const now = new Date();
    const year = now.getFullYear();
    const month = (now.getMonth() + 1).toString().padStart(2, '0');
    const day = now.getDate().toString().padStart(2, '0');
    const hours = now.getHours().toString().padStart(2, '0');
    const minutes = now.getMinutes().toString().padStart(2, '0');
    return `${year}-${month}-${day}T${hours}${minutes}`;
}

export default function NewQueryId(): string {
  return haikunator.haikunate({tokenLength: 0}) + getCurrentTimestamp();
}
