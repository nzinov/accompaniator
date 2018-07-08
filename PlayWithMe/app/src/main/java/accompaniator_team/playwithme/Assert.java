package accompaniator_team.playwithme;

public class Assert {
    public static void that(boolean condition, String message) {
        if (!condition) {
            throw new AssertionError(message);
        }
    }
    public static void that(boolean condition) {
        that(condition, "");
    }
}
