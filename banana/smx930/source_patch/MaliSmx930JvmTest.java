package dev.nxnative.android;
import java.util.ArrayList;
import java.util.List;

/** Run with plain java -ea: no Android SDK/device required. */
public final class MaliSmx930JvmTest {
    static void ok(boolean b, String msg) { if (!b) throw new AssertionError(msg); }
    static boolean contains(List<String> l, String x) { return l.contains(x); }
    public static void main(String[] a) {
        List<String> e = new ArrayList<>();
        e.add("DM_VK_IMG_RESERVE_MB=2048");
        ok(MaliSmx930.apply("SM-X930", "0400486024DEC000", e), "match");
        ok(contains(e,"DM_VK_IMG_RESERVE_MB=2048"),"existing engine setting retained");
        ok(!contains(e,"DM_VK_IMG_RESERVE_MB=1536"),"no duplicate setting");
        ok(contains(e,"DM_VK_PSO_SLOTS=1"),"compiler gate");
        ok(contains(e,"DM_MEM_FILEBACK_KINDS=shader,texture"),"file-backed shader/texture");
        int count=e.size();
        MaliSmx930.apply("SM-X930", "0400486024DEC000", e);
        ok(count==e.size(),"idempotent");
        List<String> other=new ArrayList<>();
        ok(!MaliSmx930.apply("SM-X920","0400486024DEC000",other),"different tablet");
        ok(!MaliSmx930.apply("SM-X930","other",other),"different game");
        ok(other.isEmpty(),"other game untouched");
        System.out.println("PASS SM-X930 Java policy tests");
    }
}
