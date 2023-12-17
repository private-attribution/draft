import Haikunator from "haikunator";
import { nouns, adjectives } from "./words";

const haikunator = new Haikunator({
  adjectives: adjectives,
  nouns: nouns,
});

export default function NewQueryId(): string {
  return haikunator.haikunate();
}
